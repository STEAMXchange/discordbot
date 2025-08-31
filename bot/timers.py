"""
Timer tasks for SteamXQuality Discord Bot.
Contains scheduled tasks using Nextcord task loops.
Now modular and focused only on timer management.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from nextcord.ext import tasks

# Add project root to Python path
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import our modular components
from .user_lookup import set_bot_reference
from .notifications import (
    send_assignment_notification, send_designer_assignment_notification,
    send_qc_result_notifications
)

# Set up logging
logger = logging.getLogger(__name__)

# Statistics tracking
auto_assign_stats = {
    'total_runs': 0,
    'assignments_made': 0,
    'errors': 0,
    'last_run': None
}

# Bot reference (will be set by main bot file)
bot = None


def setup_timers(bot_instance):
    """Initialize timers with bot reference."""
    global bot
    bot = bot_instance
    
    # Set bot reference for user lookup
    set_bot_reference(bot_instance)
    
    # Start all timers
    if not auto_assign_projects.is_running():
        auto_assign_projects.start()
        logger.info("✅ Auto-assignment timer started (every 5 minutes)")
    
    if not check_designer_assignments.is_running():
        check_designer_assignments.start()
        logger.info("✅ Designer phase check timer started (every 10 minutes)")
    
    if not update_spreadsheet.is_running():
        update_spreadsheet.start()
        logger.info("✅ Spreadsheet update timer started (every 15 minutes)")

    if not check_qc_results.is_running():
        check_qc_results.start()
        logger.info("✅ QC results check timer started (every 5 minutes)")


@tasks.loop(minutes=5)
async def auto_assign_projects():
    """Auto-assign resources to unconnected projects every 5 minutes."""
    try:
        logger.info("🔍 Running auto-assignment check...")
        auto_assign_stats['total_runs'] += 1
        
        # Import here to avoid issues
        from backend import auto_assign_unconnected_projects
        
        # Run the auto assignment
        results = auto_assign_unconnected_projects()
        
        # Update statistics
        auto_assign_stats['last_run'] = datetime.now().isoformat()
        assignments_this_run = results.get('successful_assignments', 0)
        auto_assign_stats['assignments_made'] += assignments_this_run
        
        # Log results
        if results.get('projects_processed', 0) > 0:
            logger.info(
                f"📊 Auto-assignment completed: "
                f"{assignments_this_run} successful, "
                f"{results.get('failed_assignments', 0)} failed, "
                f"{results.get('projects_processed', 0)} total processed"
            )
            
            # Send notification if there were assignments
            if assignments_this_run > 0:
                await send_assignment_notification(results)
        else:
            logger.info("✅ Auto-assignment check completed - no unconnected projects found")
            
    except Exception as e:
        logger.error(f"❌ Auto-assignment error: {e}")
        auto_assign_stats['errors'] += 1


@tasks.loop(minutes=10)
async def check_designer_assignments():
    """Check for projects ready for designer assignment."""
    try:
        logger.info("🎨 Checking for projects ready for designer assignment...")
        
        # Import here to avoid issues
        from backend import checkPendingDesignerAssignments, frontend_project, designer_sheet, controller_sheet
        
        # Check for pending designer assignments
        results = checkPendingDesignerAssignments(frontend_project, designer_sheet, controller_sheet)
        
        if results.get('projects_processed', 0) > 0:
            assignments_made = results.get('successful_assignments', 0)
            logger.info(
                f"🎨 Designer assignment check completed: "
                f"{assignments_made} successful, "
                f"{results.get('failed_assignments', 0)} failed, "
                f"{results.get('projects_processed', 0)} total processed"
            )
            
            # Send notification if assignments were made
            if assignments_made > 0:
                await send_designer_assignment_notification(results)
        else:
            logger.info("✅ Designer assignment check completed - no projects ready for designer assignment")
            
    except Exception as e:
        logger.error(f"❌ Designer assignment check error: {e}")


@tasks.loop(minutes=15)
async def update_spreadsheet():
    """Update spreadsheet data every 15 minutes."""
    try:
        logger.info("📊 Running spreadsheet update check...")
        
        # Import here to avoid issues
        from backend import frontend_project, get_project_info
        
        # Placeholder for spreadsheet update logic
        logger.info("📋 Checking for spreadsheet updates needed...")
        
        # Add your specific update logic here
        updates_made = 0
        
        logger.info(f"📊 Spreadsheet update completed: {updates_made} updates made")
        
    except Exception as e:
        logger.error(f"❌ Spreadsheet update error: {e}")


@tasks.loop(minutes=5)
async def check_qc_results():
    """Check for QC results and notify about pass/fail status."""
    try:
        logger.info("🔍 Checking for new QC results...")
        
        # Import here to avoid issues
        from backend import frontend_project, column_to_number, PROJECT_COLUMNS
        
        # Get all project data (skip header rows)
        all_rows = frontend_project.get_all_values()[2:]
        
        # Column positions
        project_id_col = column_to_number(PROJECT_COLUMNS.PROJECT_ID) - 1  # 0-based
        writer_qc_result_col = column_to_number(PROJECT_COLUMNS.WRITER_QC_RESULT) - 1
        design_qc_result_col = column_to_number(PROJECT_COLUMNS.DESIGN_QC_RESULT) - 1
        writer_qc_controller_col = column_to_number(PROJECT_COLUMNS.WRITER_QC_CONTROLLER) - 1
        design_qc_controller_col = column_to_number(PROJECT_COLUMNS.DESIGN_QC_CONTROLLER) - 1
        assigned_writer_col = column_to_number(PROJECT_COLUMNS.ASSIGNED_WRITER) - 1
        assigned_designer_col = column_to_number(PROJECT_COLUMNS.ASSIGNED_DESIGNER) - 1
        
        qc_notifications = []
        
        # Check each project for QC results
        for row_idx, row_data in enumerate(all_rows):
            if len(row_data) <= max(project_id_col, writer_qc_result_col, design_qc_result_col):
                continue
                
            project_id = row_data[project_id_col].strip() if project_id_col < len(row_data) else ""
            if not project_id:
                continue
                
            clean_pid = project_id.lstrip('#')
            
            # Check writer QC result
            writer_qc_result = row_data[writer_qc_result_col].strip() if writer_qc_result_col < len(row_data) else ""
            if writer_qc_result and writer_qc_result.upper() in ['PASS', 'FAIL']:
                writer = row_data[assigned_writer_col].strip() if assigned_writer_col < len(row_data) else ""
                qc_controller = row_data[writer_qc_controller_col].strip() if writer_qc_controller_col < len(row_data) else ""
                
                qc_notifications.append({
                    'project_id': clean_pid,
                    'type': 'writer',
                    'result': writer_qc_result.upper(),
                    'assignee': writer,
                    'qc_controller': qc_controller
                })
            
            # Check design QC result  
            design_qc_result = row_data[design_qc_result_col].strip() if design_qc_result_col < len(row_data) else ""
            if design_qc_result and design_qc_result.upper() in ['PASS', 'FAIL']:
                designer = row_data[assigned_designer_col].strip() if assigned_designer_col < len(row_data) else ""
                qc_controller = row_data[design_qc_controller_col].strip() if design_qc_controller_col < len(row_data) else ""
                
                qc_notifications.append({
                    'project_id': clean_pid,
                    'type': 'designer', 
                    'result': design_qc_result.upper(),
                    'assignee': designer,
                    'qc_controller': qc_controller
                })
        
        # Send QC result notifications
        if qc_notifications:
            await send_qc_result_notifications(qc_notifications)
            logger.info(f"📊 Sent {len(qc_notifications)} QC result notifications")
        else:
            logger.info("✅ No new QC results to notify about")
            
    except Exception as e:
        logger.error(f"❌ QC results check error: {e}")


def get_timer_status():
    """Get current status of all timers."""
    return {
        'auto_assign': {
            'running': auto_assign_projects.is_running(),
            'stats': auto_assign_stats.copy()
        },
        'designer_check': {
            'running': check_designer_assignments.is_running()
        },
        'spreadsheet': {
            'running': update_spreadsheet.is_running()
        },
        'qc_results': {
            'running': check_qc_results.is_running()
        }
    }