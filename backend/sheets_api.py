"""
Clean Google Sheets API interface for SteamXQuality project management.
This is the main backend interface that provides a clean API for sheet operations.
"""

import json
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
from .helpers import formatPID, getProjectRow, column_to_number, get_discord_username_from_name
from .assignment import (
    getBestDesigner, getBestWriter, assignDesigner, assignWriter,
    getAssignmentRecommendations,
    getBestController, assignWriterController, assignDesignerController,
    getControllerRecommendations, assignAll, autoAssignUnconnectedProjects
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


def auto_assign_unconnected_projects() -> Dict[str, Any]:
    """
    Automatically find and assign resources to projects that are not connected yet.
    
    Perfect for running periodically (e.g., every 5 minutes from a bot) to automatically
    process new projects that are ready for assignment.
    
    Criteria for auto-assignment:
    - PROJECT_CONNECTED is not "YES" (empty, "NO", or any other value)  
    - READY_TO_ASSIGN is "YES" (project is ready for assignment)
    - Has a valid PROJECT_ID
    
    Returns detailed summary of all assignments made.
    """
    return autoAssignUnconnectedProjects(frontend_project, designer_sheet, writer_sheet, controller_sheet)

def find_person(search_term):
    """
    Search for employee by NAME, DISCORD, or EMAIL across all departments in the same sheet
    Returns their full identity info as JSON
    
    All departments are in the same sheet with different column ranges:
    - Writers: A=NAME, B=DISCORD, C=EMAIL
    - Designers: E=NAME, F=DISCORD, G=EMAIL  
    - Quality Controllers: I=NAME, J=DISCORD, K=EMAIL
    - Management: M=NAME, N=POSITION, O=DISCORD, P=EMAIL
    """
    search_term = search_term.strip().lower()
    
    # Get the contact directory sheet (where all departments are)
    sheet = management_sheet.worksheet("Contact Directory")
    
    # Get all values from the sheet
    all_values = sheet.get_all_values()
    if len(all_values) <= 1:  # No data rows
        return json.dumps({"error": "No data found"}, indent=2)
    
    # Department configurations with their column layouts (all in same sheet)
    departments = [
        {
            'name': 'Writers',
            'name_col': 0,    # A
            'discord_col': 1, # B  
            'email_col': 2,   # C
            'position_col': None,
            'default_position': 'Writer'
        },
        {
            'name': 'Designers', 
            'name_col': 4,    # E
            'discord_col': 5, # F
            'email_col': 6,   # G
            'position_col': None,
            'default_position': 'Designer'
        },
        {
            'name': 'Quality Controllers',
            'name_col': 8,    # I
            'discord_col': 9, # J
            'email_col': 10,  # K
            'position_col': None,
            'default_position': 'Quality Controller'
        },
        {
            'name': 'Management',
            'name_col': 12,   # M
            'discord_col': 14, # O  
            'email_col': 15,  # P
            'position_col': 13, # N
            'default_position': 'Manager'
        }
    ]
    
    # Skip header row and search for the person in all departments
    for row in all_values[1:]:
        if len(row) == 0:
            continue
            
        # Check each department's columns in this row
        for dept in departments:
            # Extract fields from the row based on column positions
            name = row[dept['name_col']].strip() if dept['name_col'] < len(row) else ""
            discord = row[dept['discord_col']].strip() if dept['discord_col'] < len(row) else ""
            email = row[dept['email_col']].strip() if dept['email_col'] < len(row) else ""
            
            # Skip if this department section is empty for this row
            if not name and not discord and not email:
                continue
            
            # Get position if available
            if dept['position_col'] is not None and dept['position_col'] < len(row):
                position = row[dept['position_col']].strip() or dept['default_position']
            else:
                position = dept['default_position']
            
            # Check if search term matches any field
            if (search_term in name.lower() or 
                search_term in discord.lower() or 
                search_term in email.lower()):
                
                return json.dumps({
                    "name": name,
                    "discord": discord if discord else None,
                    "email": email,
                    "department": dept['name'],
                    "position": position,
                }, indent=2)
    
    return json.dumps({"error": "Person not found"}, indent=2)

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