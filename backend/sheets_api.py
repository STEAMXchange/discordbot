"""
Clean Google Sheets API interface for SteamXQuality project management.
This is the main backend interface that provides a clean API for sheet operations.
"""

import os
from typing import List, Dict, Any
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Import our modular components
from .models import (
    PROJECT_COLUMNS, DESIGNER_COLUMNS, WRITER_COLUMNS, CONTROLLER_COLUMNS,
    STEAMTopic, ProjectColumns, DesignerColumns, WriterColumns,
    Designer, Writer, Controller
)
from .helpers import formatPID, getProjectRow, column_to_number
from .assignment import (
    getBestDesigner, getBestWriter, assignDesigner, assignWriter,
    getAssignmentRecommendations,
    getBestController, assignWriterController, assignDesignerController,
    getControllerRecommendations, assignAll
)

# Load environment variables
load_dotenv()

# CONFIG - Now using environment variables
FRONTEND_SHEET: str = os.getenv('PROJECT_SHEET_ID', "STEAMXchange frontend management system")
MANAGEMENT_SHEET: str = os.getenv('MANAGEMENT_SHEET_ID', "STEAMXChange Management")
CREDENTIALS_FILE: str = os.getenv('GOOGLE_CREDENTIALS_FILE', "steamxquality-d4784ddb6b40.json")

# AUTH
scope: List[str] = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)  # type: ignore
client = gspread.authorize(creds)  # type: ignore

# SHEETS
frontend_sheet: gspread.Spreadsheet = client.open_by_key(FRONTEND_SHEET)
frontend_project: gspread.Worksheet = frontend_sheet.worksheet("Projects")

management_sheet: gspread.Spreadsheet = client.open_by_key(MANAGEMENT_SHEET)
contact_sheet: gspread.Worksheet = management_sheet.worksheet("Contact Directory")

# WORK SPECIFIC SHEETS
designer_sheet: gspread.Worksheet = management_sheet.worksheet("Designers")
writer_sheet: gspread.Worksheet = management_sheet.worksheet("Writers")
controller_sheet: gspread.Worksheet = management_sheet.worksheet("Quality Controllers")


# PUBLIC API FUNCTIONS
def format_project_id(pid: str | int) -> str:
    """Format a project ID to standard format."""
    return formatPID(pid)


def get_project_row(project_id: str | int) -> int:
    """Get the row number for a project ID. Returns -1 if not found."""
    return getProjectRow(project_id, frontend_project)


def get_best_designers(priority: str = "Medium") -> List[str]:
    """Get list of designers ranked by suitability for the given priority."""
    return getBestDesigner(priority, designer_sheet)


def get_best_writers(topic: str) -> List[str]:
    """Get list of writers ranked by suitability for the given topic."""
    return getBestWriter(topic, writer_sheet)


def assign_designer_to_project(project_id: str | int) -> None:
    """Assign the best available designer to a project."""
    assignDesigner(str(project_id), frontend_project, designer_sheet)


def assign_writer_to_project(project_id: str | int) -> None:
    """Assign the best available writer to a project for the given topic."""
    assignWriter(str(project_id), frontend_project, writer_sheet)


def get_assignment_recommendations(project_id: str | int,) -> Dict[str, List[str]]:
    """Get assignment recommendations without actually assigning."""
    return getAssignmentRecommendations(str(project_id), frontend_project, designer_sheet, writer_sheet)


def get_project_info(project_id: str | int) -> Dict[str, Any]:
    """Get basic project information."""
    row = get_project_row(project_id)
    if row == -1:
        return {}
    
    # Get basic project data
    project_name = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.PROJECT_NAME)).value or ""
    description = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.DESCRIPTION)).value or ""
    priority = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.PRIORITY)).value or ""
    assigned_writer = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.ASSIGNED_WRITER)).value or ""
    assigned_designer = frontend_project.cell(row, column_to_number(PROJECT_COLUMNS.ASSIGNED_DESIGNER)).value or ""
    
    return {
        "project_id": format_project_id(project_id),
        "name": project_name,
        "description": description,
        "priority": priority,
        "assigned_writer": assigned_writer,
        "assigned_designer": assigned_designer,
        "row": row
    }


# CONVENIENCE FUNCTIONS FOR COMMON OPERATIONS
def bulk_assign_writers(project_topics: List[tuple[str, str]]) -> None:
    """Bulk assign writers to multiple projects. Takes list of (project_id, topic) tuples."""
    for project_id, topic in project_topics:
        try:
            assign_writer_to_project(project_id)
        except Exception as e:
            print(f"Failed to assign writer to project {project_id}: {e}")


def bulk_assign_designers(project_ids: List[str]) -> None:
    """Bulk assign designers to multiple projects."""
    for project_id in project_ids:
        try:
            assign_designer_to_project(project_id)
        except Exception as e:
            print(f"Failed to assign designer to project {project_id}: {e}")


def get_best_controllers(speciality: str = "Writing") -> List[str]:
    """Get list of controllers ranked by suitability for the given speciality (Writing/Design)."""
    return getBestController(speciality, controller_sheet)


def assign_writer_controller_to_project(project_id: str | int) -> None:
    """Assign the best available writing controller to a project."""
    assignWriterController(str(project_id), frontend_project, controller_sheet)


def assign_design_controller_to_project(project_id: str | int) -> None:
    """Assign the best available design controller to a project."""
    assignDesignerController(str(project_id), frontend_project, controller_sheet)


def get_controller_recommendations(project_id: str | int) -> Dict[str, List[str]]:
    """Get controller recommendations for both writing and design QC without actually assigning."""
    return getControllerRecommendations(str(project_id), frontend_project, controller_sheet)


def assign_all_to_project(project_id: str | int) -> Dict[str, str]:
    """
    Assign everything needed for a project: writer, designer, and their QC controllers.
    Only assigns what's actually required based on project requirements.
    Returns a summary of what was assigned.
    """
    return assignAll(str(project_id), frontend_project, designer_sheet, writer_sheet, controller_sheet)


def get_steam_topics() -> List[str]:
    """Get available STEAM topics."""
    return [topic.value for topic in STEAMTopic]

if __name__ == "__main__":
    # Example usage of the clean API
    try:
        print("=== SteamXQuality Backend API Demo ===")
        
        # Get project info
        project_info = get_project_info("000001")
        if project_info:
            print(f"Project: {project_info['name']} (Priority: {project_info['priority']})")
        
        # Get available topics
        topics = get_steam_topics()
        print(f"Available topics: {topics}")
        
        # Get recommendations without assigning
        if project_info:
            recommendations = get_assignment_recommendations("000001")
            print(f"Top writers for Science: {recommendations['writers'][:3]}")
            print(f"Top designers: {recommendations['designers'][:3]}")
        
        # Example assignments (commented out to avoid accidental execution)
        # assign_writer_to_project("000001", "Science")
        # assign_designer_to_project("000001")
        
    except Exception as e:
        print(f"Demo error: {e}")
        print("Make sure your Google Sheets credentials and sheet IDs are configured correctly.")
