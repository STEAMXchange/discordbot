"""
Assignment engine for automatically assigning designers and writers to projects.
Contains the core logic for ranking and assigning resources.
"""

from typing import List, Dict, Any, cast
import gspread
from .models import (
    PROJECT_COLUMNS, DESIGNER_COLUMNS, WRITER_COLUMNS, CONTROLLER_COLUMNS,
    PLATFORM_HIERARCHY, TOPIC_HIERARCHY,
    Designer, Writer, Controller
)
from .helpers import (
    formatPID, getProjectRow, processDesignerRow, processWriterRow, processControllerRow, filterValidRows, column_to_number
)


def getBestDesigner(priority: str, designer_sheet: gspread.Worksheet) -> List[str]:
    """
    Returns designer names ranked best-to-worst based on KPI, platform hierarchy, and workload.
    - Sorts by score (KPI + platform bonus + principles bonus - workload penalty).
    """
    platform_rank: Dict[str, int] = {p: i for i, p in enumerate(PLATFORM_HIERARCHY)}
    all_rows: List[List[Any]] = cast(List[List[Any]], designer_sheet.get_all_values()[1:])  # skip header
    
    # Filter valid rows
    valid_rows: List[List[str]] = filterValidRows(all_rows, DESIGNER_COLUMNS.NAME)
    ranked: List[Designer] = []

    for row in valid_rows:
        try:
            designer = processDesignerRow(row, platform_rank, priority)
            ranked.append(designer)
        except Exception:
            continue

    ranked.sort(key=lambda d: -d.score)
    return [d.name for d in ranked]


def getBestWriter(topic: str, writer_sheet: gspread.Worksheet) -> List[str]:
    """
    Returns writer names ranked best-to-worst based on KPI, topic match, and workload.
    - Sorts first by topic match, then by KPI (desc), then by workload (asc).
    """
    topic_rank: Dict[str, int] = TOPIC_HIERARCHY
    all_rows: List[List[Any]] = cast(List[List[Any]], writer_sheet.get_all_values()[1:])  # skip header
    
    # Filter valid rows
    valid_rows: List[List[str]] = filterValidRows(all_rows, WRITER_COLUMNS.NAME)
    ranked: List[Writer] = []

    for row in valid_rows:
        try:
            writer = processWriterRow(row, topic_rank, topic)
            ranked.append(writer)
        except Exception:
            continue

    # Sort by score (descending)
    ranked.sort(key=lambda w: -w.score)
    return [w.name for w in ranked]


def assignDesigner(pid: str, frontend_project: gspread.Worksheet, designer_sheet: gspread.Worksheet) -> None:
    """Assign the best available designer to a project."""
    row = getProjectRow(pid, frontend_project)
    if row == -1:
        raise ValueError("Project not found")

    # check if someone is already assigned
    assign_col = column_to_number(PROJECT_COLUMNS.ASSIGNED_DESIGNER)
    already_assigned = frontend_project.cell(row, assign_col).value
    if already_assigned and already_assigned.strip():
        print(f"Project {formatPID(pid)} already assigned to {already_assigned}. Skipping.")
        return

    # get priority
    priority_col = column_to_number(PROJECT_COLUMNS.PRIORITY)
    priority = frontend_project.cell(row, priority_col).value or "None"

    # get best designers
    designers = getBestDesigner(priority, designer_sheet)
    chosen = designers[0] if designers else None
    if not chosen:
        print("No available designers to assign.")
        return

    # assign to sheet
    frontend_project.update_cell(row, assign_col, chosen)
    print(f"Assigned {formatPID(pid)} (priority: {priority}) to designer: {chosen}")


def assignWriter(pid: str, frontend_project: gspread.Worksheet, writer_sheet: gspread.Worksheet) -> None:
    """Assign the best available writer to a project based on project topic."""
    row = getProjectRow(pid, frontend_project)
    if row == -1:
        raise ValueError("Project not found")

    # check if someone is already assigned
    assign_col = column_to_number(PROJECT_COLUMNS.ASSIGNED_WRITER)
    already_assigned = frontend_project.cell(row, assign_col).value
    if already_assigned and already_assigned.strip():
        print(f"Project {formatPID(pid)} already assigned to {already_assigned}. Skipping.")
        return

    # get topic from project metadata
    topic_col = column_to_number(PROJECT_COLUMNS.WRITER_TOPIC)
    topic = frontend_project.cell(row, topic_col).value
    if not topic or not topic.strip():
        print(f"No topic specified for project {formatPID(pid)}. Cannot assign writer.")
        return
    
    topic = topic.strip()

    # get best writers for this topic
    writers = getBestWriter(topic, writer_sheet)
    chosen = writers[0] if writers else None
    if not chosen:
        print(f"No available writers to assign for topic: {topic}.")
        return

    # assign to sheet
    frontend_project.update_cell(row, assign_col, chosen)
    print(f"Assigned {formatPID(pid)} (topic: {topic}) to writer: {chosen}")


def getAssignmentRecommendations(pid: str, frontend_project: gspread.Worksheet, 
                                designer_sheet: gspread.Worksheet, writer_sheet: gspread.Worksheet) -> Dict[str, List[str]]:
    """Get assignment recommendations for both writer and designer without actually assigning."""
    row = getProjectRow(pid, frontend_project)
    if row == -1:
        raise ValueError("Project not found")

    # get priority for designer recommendations
    priority_col = column_to_number(PROJECT_COLUMNS.PRIORITY)
    priority = frontend_project.cell(row, priority_col).value or "None"
    
    # get topic from project metadata for writer recommendations
    topic_col = column_to_number(PROJECT_COLUMNS.WRITER_TOPIC)
    topic = frontend_project.cell(row, topic_col).value
    if not topic or not topic.strip():
        topic = "Science"  # Default fallback topic
    else:
        topic = topic.strip()

    return {
        "writers": getBestWriter(topic, writer_sheet)[:5],  # Top 5 writers
        "designers": getBestDesigner(priority, designer_sheet)[:5]  # Top 5 designers
    }


def getBestController(speciality: str, controller_sheet: gspread.Worksheet) -> List[str]:
    """
    Returns controller names ranked best-to-worst based on KPI, speciality match, and workload.
    - Speciality should be "Writing" or "Design"
    - Sorts by score (KPI - workload penalty), with speciality match as filter.
    """
    all_rows: List[List[Any]] = cast(List[List[Any]], controller_sheet.get_all_values()[1:])  # skip header
    
    # Filter valid rows
    valid_rows: List[List[str]] = filterValidRows(all_rows, CONTROLLER_COLUMNS.NAME)
    ranked: List[Controller] = []

    for row in valid_rows:
        try:
            controller = processControllerRow(row, speciality)
            # Only include controllers that match the speciality or can handle both
            if controller.speciality.upper() in [speciality.upper(), "BOTH", "ANY"]:
                ranked.append(controller)
        except Exception:
            continue

    # Sort by score (descending)
    ranked.sort(key=lambda c: -c.score)
    return [c.name for c in ranked]


def assignWriterController(pid: str, frontend_project: gspread.Worksheet, controller_sheet: gspread.Worksheet) -> None:
    """Assign the best available writing controller to a project."""
    row = getProjectRow(pid, frontend_project)
    if row == -1:
        raise ValueError("Project not found")

    # check if someone is already assigned
    assign_col = column_to_number(PROJECT_COLUMNS.WRITER_QC_CONTROLLER)
    already_assigned = frontend_project.cell(row, assign_col).value
    if already_assigned and already_assigned.strip():
        print(f"Project {formatPID(pid)} already has writer controller assigned: {already_assigned}. Skipping.")
        return

    # get best controllers for writing
    controllers = getBestController("Writing", controller_sheet)
    chosen = controllers[0] if controllers else None
    if not chosen:
        print("No available writing controllers to assign.")
        return

    # assign to sheet
    frontend_project.update_cell(row, assign_col, chosen)
    print(f"Assigned {formatPID(pid)} writer QC to controller: {chosen}")


def assignDesignerController(pid: str, frontend_project: gspread.Worksheet, controller_sheet: gspread.Worksheet) -> None:
    """Assign the best available design controller to a project."""
    row = getProjectRow(pid, frontend_project)
    if row == -1:
        raise ValueError("Project not found")

    # check if someone is already assigned
    assign_col = column_to_number(PROJECT_COLUMNS.DESIGN_QC_CONTROLLER)
    already_assigned = frontend_project.cell(row, assign_col).value
    if already_assigned and already_assigned.strip():
        print(f"Project {formatPID(pid)} already has design controller assigned: {already_assigned}. Skipping.")
        return

    # get best controllers for design
    controllers = getBestController("Design", controller_sheet)
    chosen = controllers[0] if controllers else None
    if not chosen:
        print("No available design controllers to assign.")
        return

    # assign to sheet
    frontend_project.update_cell(row, assign_col, chosen)
    print(f"Assigned {formatPID(pid)} design QC to controller: {chosen}")


def getControllerRecommendations(pid: str, frontend_project: gspread.Worksheet, controller_sheet: gspread.Worksheet) -> Dict[str, List[str]]:
    """Get controller recommendations for both writing and design QC without actually assigning."""
    row = getProjectRow(pid, frontend_project)
    if row == -1:
        raise ValueError("Project not found")

    return {
        "writer_controllers": getBestController("Writing", controller_sheet)[:5],  # Top 5 writing controllers
        "design_controllers": getBestController("Design", controller_sheet)[:5]  # Top 5 design controllers
    }


def assignAll(pid: str, frontend_project: gspread.Worksheet, designer_sheet: gspread.Worksheet, 
              writer_sheet: gspread.Worksheet, controller_sheet: gspread.Worksheet) -> Dict[str, str]:
    """
    Assign everything needed for a project: writer, designer, and their QC controllers.
    Only assigns what's actually required based on project requirements.
    Returns a summary of what was assigned.
    """
    row = getProjectRow(pid, frontend_project)
    if row == -1:
        raise ValueError("Project not found")

    results = {
        "writer": "Not required",
        "writer_controller": "Not required", 
        "designer": "Not required",
        "design_controller": "Not required"
    }

    # Check what's required for this project
    writer_required_col = column_to_number(PROJECT_COLUMNS.WRITER_REQUIRED)
    designer_required_col = column_to_number(PROJECT_COLUMNS.DESIGNER_REQUIRED)
    
    writer_required = frontend_project.cell(row, writer_required_col).value
    designer_required = frontend_project.cell(row, designer_required_col).value
    
    # Normalize the values (handle YES/NO, True/False, etc.)
    writer_needed = str(writer_required).upper() in ['YES', 'TRUE', '1', 'Y']
    designer_needed = str(designer_required).upper() in ['YES', 'TRUE', '1', 'Y']

    print(f"🎯 Assigning all resources for project {formatPID(pid)}")
    print(f"   Writer needed: {writer_needed}")
    print(f"   Designer needed: {designer_needed}")

    # Assign writer and writer controller if needed
    if writer_needed:
        try:
            assignWriter(pid, frontend_project, writer_sheet)
            results["writer"] = "Assigned"
            
            # Assign writer controller after writer is assigned
            try:
                assignWriterController(pid, frontend_project, controller_sheet)
                results["writer_controller"] = "Assigned"
            except Exception as e:
                results["writer_controller"] = f"Failed: {str(e)}"
                print(f"⚠️  Writer controller assignment failed: {e}")
                
        except Exception as e:
            results["writer"] = f"Failed: {str(e)}"
            results["writer_controller"] = "Skipped (no writer)"
            print(f"⚠️  Writer assignment failed: {e}")

    # Assign designer and design controller if needed
    if designer_needed:
        try:
            assignDesigner(pid, frontend_project, designer_sheet)
            results["designer"] = "Assigned"
            
            # Assign design controller after designer is assigned
            try:
                assignDesignerController(pid, frontend_project, controller_sheet)
                results["design_controller"] = "Assigned"
            except Exception as e:
                results["design_controller"] = f"Failed: {str(e)}"
                print(f"⚠️  Design controller assignment failed: {e}")
                
        except Exception as e:
            results["designer"] = f"Failed: {str(e)}"
            results["design_controller"] = "Skipped (no designer)"
            print(f"⚠️  Designer assignment failed: {e}")

    print(f"✅ Assignment completed for project {formatPID(pid)}")
    print(f"   📝 Writer: {results['writer']}")
    print(f"   🔍 Writer QC: {results['writer_controller']}")
    print(f"   🎨 Designer: {results['designer']}")
    print(f"   🔍 Design QC: {results['design_controller']}")
    
    return results


def autoAssignUnconnectedProjects(frontend_project: gspread.Worksheet, designer_sheet: gspread.Worksheet,
                                 writer_sheet: gspread.Worksheet, controller_sheet: gspread.Worksheet) -> Dict[str, Any]:
    """
    Automatically find and assign resources to projects that are not connected yet.
    
    Criteria for auto-assignment:
    - PROJECT_CONNECTED is not "YES" (empty, "NO", or any other value)
    - READY_TO_ASSIGN is "YES" (project is ready for assignment)
    - Has a valid PROJECT_ID
    
    Returns summary of all assignments made.
    """
    print("🔍 Scanning for unconnected projects ready for assignment...")
    
    # Get all project data (skip header row)
    all_rows = frontend_project.get_all_values()[2:]  # Skip 2 header rows
    
    # Column positions
    project_id_col = column_to_number(PROJECT_COLUMNS.PROJECT_ID) - 1  # 0-based
    ready_to_assign_col = column_to_number(PROJECT_COLUMNS.READY_TO_ASSIGN) - 1
    project_connected_col = column_to_number(PROJECT_COLUMNS.PROJECT_CONNECTED) - 1
    
    unconnected_projects = []
    assignment_results = {}
    
    # Find unconnected projects that are ready to assign
    for row_idx, row_data in enumerate(all_rows):
        if len(row_data) <= max(project_id_col, ready_to_assign_col, project_connected_col):
            continue  # Skip rows that don't have enough columns
            
        project_id = row_data[project_id_col].strip() if project_id_col < len(row_data) else ""
        ready_to_assign = row_data[ready_to_assign_col].strip() if ready_to_assign_col < len(row_data) else ""
        project_connected = row_data[project_connected_col].strip() if project_connected_col < len(row_data) else ""
        
        # Check if project meets criteria for auto-assignment
        if (project_id and 
            ready_to_assign.upper() in ['YES', 'TRUE', '1', 'Y'] and
            project_connected.upper() not in ['YES', 'TRUE', '1', 'Y']):
            
            # Clean up project ID (remove # if present)
            clean_pid = project_id.lstrip('#')
            unconnected_projects.append(clean_pid)
    
    print(f"📋 Found {len(unconnected_projects)} unconnected projects ready for assignment:")
    for pid in unconnected_projects:
        print(f"   • {formatPID(pid)}")
    
    if not unconnected_projects:
        print("✅ No unconnected projects found that are ready for assignment.")
        return {"projects_processed": 0, "assignments": {}}
    
    # Auto-assign resources to each unconnected project
    for pid in unconnected_projects:
        try:
            print(f"\n🚀 Auto-assigning resources to project {formatPID(pid)}...")
            
            # Use our existing assignAll function
            results = assignAll(pid, frontend_project, designer_sheet, writer_sheet, controller_sheet)
            assignment_results[pid] = results
            
            # Mark project as connected after successful assignment
            try:
                row = getProjectRow(pid, frontend_project)
                if row != -1:
                    connected_col = column_to_number(PROJECT_COLUMNS.PROJECT_CONNECTED)
                    frontend_project.update_cell(row, connected_col, "YES")
                    print(f"✅ Marked project {formatPID(pid)} as CONNECTED")
            except Exception as e:
                print(f"⚠️  Failed to mark project {formatPID(pid)} as connected: {e}")
                
        except Exception as e:
            print(f"❌ Failed to auto-assign project {formatPID(pid)}: {e}")
            assignment_results[pid] = {"error": str(e)}
    
    # Summary
    successful_assignments = sum(1 for result in assignment_results.values() if "error" not in result)
    failed_assignments = len(assignment_results) - successful_assignments
    
    print(f"\n📊 Auto-Assignment Summary:")
    print(f"   ✅ Successfully processed: {successful_assignments} projects")
    print(f"   ❌ Failed: {failed_assignments} projects")
    print(f"   🔗 All successful projects marked as CONNECTED")
    
    return {
        "projects_processed": len(unconnected_projects),
        "successful_assignments": successful_assignments,
        "failed_assignments": failed_assignments,
        "assignments": assignment_results
    }