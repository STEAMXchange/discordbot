"""
Assignment engine for automatically assigning designers and writers to projects.
Contains the core logic for ranking and assigning resources.
"""

from typing import List, Dict, Any, cast
import gspread
from .models import (
    PROJECT_COLUMNS, DESIGNER_COLUMNS, WRITER_COLUMNS,
    PLATFORM_HIERARCHY, TOPIC_HIERARCHY,
    Designer, Writer
)
from .helpers import (
    formatPID, getProjectRow, processDesignerRow, processWriterRow, filterValidRows
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
    assign_col = ord(PROJECT_COLUMNS.ASSIGNED_DESIGNER) - ord('A') + 1
    already_assigned = frontend_project.cell(row, assign_col).value
    if already_assigned and already_assigned.strip():
        print(f"Project {formatPID(pid)} already assigned to {already_assigned}. Skipping.")
        return

    # get priority
    priority_col = ord(PROJECT_COLUMNS.PRIORITY) - ord('A') + 1
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


def assignWriter(pid: str, topic: str, frontend_project: gspread.Worksheet, writer_sheet: gspread.Worksheet) -> None:
    """Assign the best available writer to a project based on topic."""
    row = getProjectRow(pid, frontend_project)
    if row == -1:
        raise ValueError("Project not found")

    # check if someone is already assigned
    assign_col = ord(PROJECT_COLUMNS.ASSIGNED_WRITER) - ord('A') + 1
    already_assigned = frontend_project.cell(row, assign_col).value
    if already_assigned and already_assigned.strip():
        print(f"Project {formatPID(pid)} already assigned to {already_assigned}. Skipping.")
        return

    # get best writers for this topic
    writers = getBestWriter(topic, writer_sheet)
    chosen = writers[0] if writers else None
    if not chosen:
        print("No available writers to assign.")
        return

    # assign to sheet
    frontend_project.update_cell(row, assign_col, chosen)
    print(f"Assigned {formatPID(pid)} (topic: {topic}) to writer: {chosen}")


def getAssignmentRecommendations(pid: str, topic: str, frontend_project: gspread.Worksheet, 
                                designer_sheet: gspread.Worksheet, writer_sheet: gspread.Worksheet) -> Dict[str, List[str]]:
    """Get assignment recommendations for both writer and designer without actually assigning."""
    row = getProjectRow(pid, frontend_project)
    if row == -1:
        raise ValueError("Project not found")

    # get priority for designer recommendations
    priority_col = ord(PROJECT_COLUMNS.PRIORITY) - ord('A') + 1
    priority = frontend_project.cell(row, priority_col).value or "None"

    return {
        "writers": getBestWriter(topic, writer_sheet)[:5],  # Top 5 writers
        "designers": getBestDesigner(priority, designer_sheet)[:5]  # Top 5 designers
    }
