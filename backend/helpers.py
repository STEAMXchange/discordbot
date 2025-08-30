"""
Helper functions for Google Sheets operations.
Contains utility functions for data processing and sheet interactions.
"""

from typing import Union, List, Dict, Any, cast
import gspread
from .models import (
    PROJECT_COLUMNS, DESIGNER_COLUMNS, WRITER_COLUMNS,
    PLATFORM_HIERARCHY, TOPIC_HIERARCHY,
    Designer, Writer
)


def formatPID(pid: Union[str, int]) -> str:
    """
    Formats your PID so it can work with other functions.
    """
    # normalize to int first
    if isinstance(pid, str):
        # strip any leading '#' and whitespace
        pid = pid.strip().lstrip("#")
    try:
        num: int = int(pid)
    except ValueError as e:
        raise ValueError(f"Invalid project ID: {pid}") from e

    if num < 0 or num > 999999:
        raise ValueError("Project ID must be between 0 and 999999")

    return f"#{num:06d}"


def getProjectRow(project_id: Union[str, int], frontend_project: gspread.Worksheet) -> int:
    """
    Return 1-based row of the given PID in column A, or -1 if not found.
    Always coerces values to string before strip/lstrip.
    """
    # normalize input
    pid: str = str(project_id).strip().lstrip("'")
    if not pid.startswith("#") and pid.isdigit():
        pid = formatPID(pid)  # from earlier

    col_vals = frontend_project.col_values(1)  # column A

    for row_num, val in enumerate(col_vals[2:], start=3):  # skip 2 header rows
        cell_pid: str = str(val).strip().lstrip("'")
        if cell_pid == pid:
            return row_num

    return -1


def getWorkloadPenalty(priority: str, open_tasks: int) -> int:
    """Calculate workload penalty based on priority and open tasks."""
    priority = priority.strip().capitalize()
    match priority:
        case "High":
            return 10 * open_tasks  # heavy penalty
        case "Medium":
            return 6 * open_tasks
        case "Low":
            return 3 * open_tasks
        case "None" | _:
            return 1 * open_tasks


def getTopicPenalty(required_topic: str, writer_category: str) -> int:
    """Calculate penalty based on topic match."""
    required_topic = required_topic.strip().capitalize()
    writer_category = writer_category.strip().upper()
    
    # Perfect match gets no penalty
    if required_topic.upper() == writer_category:
        return 0
    
    # ANY can handle anything but with slight penalty
    if writer_category == "ANY":
        return 2
    
    # DO NOT ASSIGN gets huge penalty
    if writer_category == "DO NOT ASSIGN":
        return 1000
    
    # Mismatch gets moderate penalty
    return 10


def processDesignerRow(row: List[str], platform_rank: Dict[str, int], priority: str) -> Designer:
    """Process a single designer row from the sheet."""
    def get(col: str) -> str:
        idx = ord(getattr(DESIGNER_COLUMNS, col)) - ord('A')
        return row[idx].strip() if idx < len(row) else ""

    name = get('NAME')
    platform = get('PLATFORM')
    kpi = float(get('KPI') or 0)
    design_principles = get('DESIGN_PRINCIPLES').upper() == 'YES'

    assigned_work = [pid.strip() for pid in get('ASSIGNED_WORK').split(',') if pid.strip()]
    finished_work = [pid.strip() for pid in get('DESIGNS_FINISHED').split(',') if pid.strip()]
    open_tasks = len(set(assigned_work) - set(finished_work))

    platform_bonus = max(0, 5 - platform_rank.get(platform, len(PLATFORM_HIERARCHY)))
    principles_bonus = 3 if design_principles else 0  # bonus for knowing design theory
    workload_penalty = getWorkloadPenalty(priority, open_tasks)
    score = kpi + platform_bonus + principles_bonus - workload_penalty

    return Designer(
        name=name,
        platform=platform,
        assigned_work=assigned_work,
        designs_finished=finished_work,
        num_finished=len(finished_work),
        quality_percent=0.0,
        avg_turnaround_time=0.0,
        kpi=kpi,
        platform_rank=platform_rank.get(platform, len(PLATFORM_HIERARCHY)),
        open_tasks=open_tasks,
        score=score
    )


def processWriterRow(row: List[str], topic_rank: Dict[str, int], topic: str) -> Writer:
    """Process a single writer row from the sheet."""
    def get(col: str) -> str:
        idx = ord(getattr(WRITER_COLUMNS, col)) - ord('A')
        return row[idx].strip() if idx < len(row) else ""

    name = get('NAME')
    category = get('CATEGORY')
    kpi = float(get('KPI') or 0)

    assigned_work = [pid.strip() for pid in get('ASSIGNED_WORK').split(',') if pid.strip()]
    finished_work = [pid.strip() for pid in get('WRITINGS_FINISHED').split(',') if pid.strip()]
    open_tasks = len(set(assigned_work) - set(finished_work))

    # Calculate topic bonus/penalty
    topic_penalty = getTopicPenalty(topic, category)
    workload_penalty = getWorkloadPenalty("Medium", open_tasks)  # Use medium priority for workload calc
    score = kpi - topic_penalty - workload_penalty

    return Writer(
        name=name,
        category=category,
        assigned_work=assigned_work,
        writings_finished=finished_work,
        num_finished=len(finished_work),
        quality_percent=0.0,
        avg_turnaround_time=0.0,
        kpi=kpi,
        topic_rank=topic_rank.get(category, len(TOPIC_HIERARCHY)),
        open_tasks=open_tasks,
        score=score
    )


def filterValidRows(sheet_data: List[List[Any]], name_column: str) -> List[List[str]]:
    """Filter and convert sheet data to valid string rows."""
    valid_rows: List[List[str]] = []
    for row_data in sheet_data:
        if len(row_data) > 0:
            name_idx = ord(name_column) - ord('A')
            if name_idx < len(row_data) and str(row_data[name_idx]).strip():
                valid_rows.append([str(cell) for cell in row_data])
    return valid_rows
