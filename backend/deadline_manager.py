"""
Automatic Deadline Management System for SteamXQuality.

This module handles automatic calculation of sub-deadlines for projects,
ensuring proper phase sequencing and QC time allocation.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

from .models import PROJECT_COLUMNS
from .helpers import column_to_number, getProjectRow, formatPID

# Set up logging
logger = logging.getLogger(__name__)


class ProjectPhase(Enum):
    """Project phase enumeration."""
    WRITING = "writing"
    WRITING_QC = "writing_qc"
    DESIGN = "design"
    DESIGN_QC = "design_qc"
    COMPLETE = "complete"


@dataclass
class PhaseDeadlines:
    """Container for all phase deadlines."""
    project_deadline: datetime
    writing_deadline: datetime
    writing_qc_deadline: datetime
    design_deadline: datetime
    design_qc_deadline: datetime
    
    # Calculated durations
    writing_days: int
    writing_qc_days: int
    design_days: int
    design_qc_days: int
    total_days: int


@dataclass
class DeadlineConfig:
    """Configuration for deadline calculation."""
    # Default time allocations (in days)
    writing_base_days: int = 7      # Base writing time
    writing_qc_days: int = 3        # QC time for writing
    design_base_days: int = 5       # Base design time
    design_qc_days: int = 3         # QC time for design
    min_qc_days: int = 1            # Minimum QC time if padding needed
    
    # Priority multipliers for writing/design time
    priority_multipliers: Dict[str, float] = None
    
    def __post_init__(self):
        if self.priority_multipliers is None:
            self.priority_multipliers = {
                "High": 0.8,      # Rush jobs get less time
                "Medium": 1.0,    # Standard time
                "Low": 1.2        # More time for low priority
            }


class DeadlineManager:
    """Manages automatic deadline calculation and phase sequencing."""
    
    def __init__(self, config: Optional[DeadlineConfig] = None):
        self.config = config or DeadlineConfig()
    
    def calculate_phase_deadlines(self, 
                                project_deadline: datetime,
                                priority: str = "Medium",
                                needs_writer: bool = True,
                                needs_designer: bool = True) -> PhaseDeadlines:
        """
        Calculate all phase deadlines working backwards from project deadline.
        
        Args:
            project_deadline: The final project deadline
            priority: Project priority ("High", "Medium", "Low")
            needs_writer: Whether project needs a writer
            needs_designer: Whether project needs a designer
            
        Returns:
            PhaseDeadlines object with all calculated deadlines
        """
        logger.info(f"Calculating deadlines for project with deadline: {project_deadline}")
        
        # Get priority multiplier
        priority_mult = self.config.priority_multipliers.get(priority, 1.0)
        
        # Calculate base durations
        writing_days = int(self.config.writing_base_days * priority_mult) if needs_writer else 0
        design_days = int(self.config.design_base_days * priority_mult) if needs_designer else 0
        
        # QC days are fixed (don't scale with priority)
        writing_qc_days = self.config.writing_qc_days if needs_writer else 0
        design_qc_days = self.config.design_qc_days if needs_designer else 0
        
        # Calculate total time needed
        total_days = writing_days + writing_qc_days + design_days + design_qc_days
        
        # Check if we have enough time
        available_days = (project_deadline - datetime.now()).days
        if available_days < total_days:
            logger.warning(f"Not enough time! Need {total_days} days, have {available_days}")
            # Try to compress by reducing QC time
            writing_qc_days, design_qc_days = self._compress_qc_time(
                available_days, writing_days, design_days, needs_writer, needs_designer
            )
            total_days = writing_days + writing_qc_days + design_days + design_qc_days
        
        # Calculate deadlines working backwards
        design_qc_deadline = project_deadline
        design_deadline = design_qc_deadline - timedelta(days=design_qc_days) if needs_designer else project_deadline
        writing_qc_deadline = design_deadline - timedelta(days=design_days) if needs_designer else design_deadline
        writing_deadline = writing_qc_deadline - timedelta(days=writing_qc_days) if needs_writer else writing_qc_deadline
        
        # If no writing needed, adjust accordingly
        if not needs_writer:
            writing_deadline = writing_qc_deadline = design_deadline - timedelta(days=design_days) if needs_designer else project_deadline
        
        deadlines = PhaseDeadlines(
            project_deadline=project_deadline,
            writing_deadline=writing_deadline,
            writing_qc_deadline=writing_qc_deadline,
            design_deadline=design_deadline,
            design_qc_deadline=design_qc_deadline,
            writing_days=writing_days,
            writing_qc_days=writing_qc_days,
            design_days=design_days,
            design_qc_days=design_qc_days,
            total_days=total_days
        )
        
        logger.info(f"Calculated deadlines: Writing: {writing_deadline}, Design: {design_deadline}")
        return deadlines
    
    def _compress_qc_time(self, available_days: int, writing_days: int, design_days: int,
                         needs_writer: bool, needs_designer: bool) -> Tuple[int, int]:
        """
        Try to compress QC time if not enough days available.
        Maintains minimum QC time while fitting within available days.
        """
        core_work_days = writing_days + design_days
        qc_days_available = available_days - core_work_days
        
        if qc_days_available < 0:
            logger.error(f"Not enough time even for core work! Need {core_work_days}, have {available_days}")
            # Emergency compression - minimum viable QC
            return (self.config.min_qc_days if needs_writer else 0,
                   self.config.min_qc_days if needs_designer else 0)
        
        # Distribute available QC days
        if needs_writer and needs_designer:
            # Split QC time between writing and design
            writing_qc = min(self.config.writing_qc_days, qc_days_available // 2)
            design_qc = min(self.config.design_qc_days, qc_days_available - writing_qc)
            
            # Ensure minimum QC time
            writing_qc = max(writing_qc, self.config.min_qc_days)
            design_qc = max(design_qc, self.config.min_qc_days)
            
        elif needs_writer:
            writing_qc = min(self.config.writing_qc_days, qc_days_available)
            writing_qc = max(writing_qc, self.config.min_qc_days)
            design_qc = 0
            
        elif needs_designer:
            design_qc = min(self.config.design_qc_days, qc_days_available)
            design_qc = max(design_qc, self.config.min_qc_days)
            writing_qc = 0
        else:
            writing_qc = design_qc = 0
        
        logger.info(f"Compressed QC time: Writing QC: {writing_qc} days, Design QC: {design_qc} days")
        return writing_qc, design_qc
    
    def get_current_phase(self, project_id: str, frontend_project) -> ProjectPhase:
        """
        Determine the current phase of a project based on completion dates.
        """
        row = getProjectRow(project_id, frontend_project)
        if row == -1:
            raise ValueError(f"Project {project_id} not found")
        
        # Check completion dates
        writer_done = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.WRITER_DONE_DATE)).value
        writer_qc_done = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.WRITER_QC_EXIT_DATE)).value
        design_done = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.DESIGN_DONE_DATE)).value
        design_qc_done = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.DESIGN_QC_EXIT_DATE)).value
        project_done = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.PROJECT_DONE)).value
        
        # Determine phase based on what's completed
        if project_done and project_done.upper() == "YES":
            return ProjectPhase.COMPLETE
        elif design_qc_done:
            return ProjectPhase.COMPLETE
        elif design_done:
            return ProjectPhase.DESIGN_QC
        elif writer_qc_done:
            return ProjectPhase.DESIGN
        elif writer_done:
            return ProjectPhase.WRITING_QC
        else:
            return ProjectPhase.WRITING
    
    def should_contact_designer(self, project_id: str, frontend_project) -> bool:
        """
        Check if designer should be contacted (writing phase must be complete).
        Returns True if writing QC is done or if no writer is required.
        """
        row = getProjectRow(project_id, frontend_project)
        if row == -1:
            return False
        
        # Check if writer is required
        writer_required = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.WRITER_REQUIRED)).value
        if not writer_required or writer_required.upper() != "YES":
            return True  # No writer needed, designer can start
        
        # Writer is required, check if writing QC is complete
        writer_qc_done = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.WRITER_QC_EXIT_DATE)).value
        return bool(writer_qc_done and writer_qc_done.strip())
    
    def update_project_deadlines(self, project_id: str, frontend_project, auto_calculate: bool = True):
        """
        Update project deadlines in the spreadsheet.
        
        Args:
            project_id: Project ID to update
            frontend_project: Frontend project worksheet
            auto_calculate: Whether to automatically calculate deadlines based on project deadline
        """
        try:
            row = getProjectRow(project_id, frontend_project)
            if row == -1:
                logger.error(f"Project {project_id} not found")
                return False
            
            # Get project info
            priority = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.PRIORITY)).value or "Medium"
            writer_required = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.WRITER_REQUIRED)).value
            designer_required = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.DESIGNER_REQUIRED)).value
            project_deadline_str = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.PROJECT_DEADLINE)).value
            
            if not project_deadline_str or not auto_calculate:
                logger.info(f"No project deadline set or auto-calculate disabled for {project_id}")
                return False
            
            # Parse project deadline
            try:
                project_deadline = datetime.strptime(project_deadline_str.strip(), "%Y-%m-%d")
            except ValueError:
                try:
                    project_deadline = datetime.strptime(project_deadline_str.strip(), "%m/%d/%Y")
                except ValueError:
                    logger.error(f"Invalid project deadline format: {project_deadline_str}")
                    return False
            
            # Calculate phase deadlines
            needs_writer = writer_required and writer_required.upper() == "YES"
            needs_designer = designer_required and designer_required.upper() == "YES"
            
            deadlines = self.calculate_phase_deadlines(
                project_deadline=project_deadline,
                priority=priority,
                needs_writer=needs_writer,
                needs_designer=needs_designer
            )
            
            # Update deadlines in spreadsheet
            updates = []
            if needs_writer:
                updates.append({
                    'range': f"{PROJECT_COLUMNS.WRITER_DEADLINE}{row}",
                    'values': [[deadlines.writing_deadline.strftime("%Y-%m-%d")]]
                })
            
            if needs_designer:
                updates.append({
                    'range': f"{PROJECT_COLUMNS.DESIGN_DEADLINE}{row}",
                    'values': [[deadlines.design_deadline.strftime("%Y-%m-%d")]]
                })
            
            # Batch update
            if updates:
                frontend_project.batch_update(updates)
                logger.info(f"Updated deadlines for project {project_id}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to update deadlines for project {project_id}: {e}")
            return False
    
    def get_deadline_summary(self, project_id: str, frontend_project) -> Dict[str, Any]:
        """Get a summary of all deadlines for a project."""
        try:
            row = getProjectRow(project_id, frontend_project)
            if row == -1:
                return {"error": f"Project {project_id} not found"}
            
            # Get all deadline information
            project_deadline = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.PROJECT_DEADLINE)).value
            writer_deadline = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.WRITER_DEADLINE)).value
            design_deadline = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.DESIGN_DEADLINE)).value
            
            current_phase = self.get_current_phase(project_id, frontend_project)
            can_contact_designer = self.should_contact_designer(project_id, frontend_project)
            
            return {
                "project_id": formatPID(project_id),
                "project_deadline": project_deadline,
                "writer_deadline": writer_deadline,
                "design_deadline": design_deadline,
                "current_phase": current_phase.value,
                "can_contact_designer": can_contact_designer,
                "days_until_deadline": (datetime.strptime(project_deadline, "%Y-%m-%d") - datetime.now()).days if project_deadline else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get deadline summary for {project_id}: {e}")
            return {"error": str(e)}


# Create default deadline manager instance
default_deadline_manager = DeadlineManager()


# Public API functions
def calculate_project_deadlines(project_deadline: datetime, 
                              priority: str = "Medium",
                              needs_writer: bool = True,
                              needs_designer: bool = True) -> PhaseDeadlines:
    """Calculate phase deadlines for a project."""
    return default_deadline_manager.calculate_phase_deadlines(
        project_deadline, priority, needs_writer, needs_designer
    )


def update_project_deadlines(project_id: str, frontend_project):
    """Update project deadlines in spreadsheet."""
    return default_deadline_manager.update_project_deadlines(project_id, frontend_project)


def should_contact_designer(project_id: str, frontend_project) -> bool:
    """Check if designer should be contacted."""
    return default_deadline_manager.should_contact_designer(project_id, frontend_project)


def get_current_phase(project_id: str, frontend_project) -> ProjectPhase:
    """Get current phase of a project."""
    return default_deadline_manager.get_current_phase(project_id, frontend_project)


def get_deadline_summary(project_id: str, frontend_project) -> Dict[str, Any]:
    """Get deadline summary for a project."""
    return default_deadline_manager.get_deadline_summary(project_id, frontend_project)

