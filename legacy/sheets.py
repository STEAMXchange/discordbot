from dataclasses import dataclass
from typing import List, Dict, Union, Any, cast
from enum import Enum
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv

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

@dataclass(frozen=True)
class ProjectColumns:
    # INFO
    PROJECT_ID: str =               "A"
    PROJECT_NAME: str =             "B"
    DESCRIPTION: str =              "C"
    PRIORITY: str =                 "D"
    WRITER_REQUIRED: str =          "E"  # was "WRITER?"
    DESIGNER_REQUIRED: str =        "F"  # was "DESIGNER?"
    READY_TO_ASSIGN: str =          "G"

    # WRITERS
    ASSIGNED_WRITER: str =          "I"
    DOCUMENT_LINK: str =            "J"
    WRITER_DEADLINE: str =          "K"
    WRITER_SEND_METHOD: str =       "L"

    # WRITER QC
    WRITER_QC_CONTROLLER: str =     "N"
    WRITER_QC_FORM_POST: str =      "O"
    WRITER_QC_REVISION_COUNT: str = "P"
    WRITER_QC_RESULT: str =         "Q"

    # DESIGNERS
    ASSIGNED_DESIGNER: str =        "S"
    MEDIA_LINK: str =               "T"
    DESIGN_DEADLINE: str =          "U"
    DESIGN_SEND_METHOD: str =       "V"

    # DESIGNER QC
    DESIGN_QC_CONTROLLER: str =     "X"
    DESIGN_QC_FORM_POST: str =      "Y"
    DESIGN_QC_REVISION_COUNT: str = "Z"
    DESIGN_QC_RESULT: str =         "AA"

    # METADATA
    PROJECT_START_DATE: str =       "AC"
    WRITER_TOPIC: str =             "AC"
    WRITER_DONE_DATE: str =         "AD"
    WRITER_QC_EXIT_DATE: str =      "AE"
    DESIGN_DONE_DATE: str =         "AF"
    DESIGN_QC_EXIT_DATE: str =      "AG"
    PROJECT_END_DATE: str =         "AH"

# Create a singleton instance for use throughout the codebase
PROJECT_COLUMNS = ProjectColumns()

# STEAM Topic Enumeration
class STEAMTopic(Enum):
    SCIENCE = "Science"
    TECHNOLOGY = "Technology" 
    ENGINEERING = "Engineering"
    ART = "Art"
    ANY = "ANY"  # Can handle any topic
    DO_NOT_ASSIGN = "DO NOT ASSIGN"  # Should not be assigned work

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

def getProjectRow(project_id: Union[str, int]) -> int:
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

# DESIGNER SPECIFIC STUFF

@dataclass
class Designer:
    name:                   str
    platform:               str
    assigned_work:          List[str]
    designs_finished:       List[str]
    num_finished:           int
    quality_percent:        float
    avg_turnaround_time:    float
    kpi:                    float
    platform_rank:          int
    open_tasks:             int = 0
    score:                  float = 0.0

@dataclass(frozen=True)
class DesignerColumns:
    NAME: str =                 'A'
    PLATFORM: str =             'B'
    ASSIGNED_WORK: str =        'C'  # list of PIDs
    DESIGNS_FINISHED: str =     'D'  # list of PIDs
    NUM_FINISHED: str =         'E'  # count
    QUALITY_PERCENT: str =      'I'
    AVG_TURNAROUND_TIME: str =  'J'
    KPI: str =                  'K'
    DESIGN_PRINCIPLES: str =     'M' # YES / NO


# Create a singleton instance for use throughout the codebase
DESIGNER_COLUMNS = DesignerColumns()

# Platform hierarchy for designer ranking
PLATFORM_HIERARCHY: List[str] = [
    "Adobe",        # TOP PICK
    "Figma",
    "Canva",
    "ProCreate",
    "Sketch",
    "Variety",
    "Other",        # LAST PICK
]

def getWorkloadPenalty(priority: str, open_tasks: int) -> int:
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

def getBestDesigner(priority: str) -> List[str]:
    platform_rank: Dict[str, int] = {p: i for i, p in enumerate(PLATFORM_HIERARCHY)}
    all_rows: List[List[Any]] = cast(List[List[Any]], designer_sheet.get_all_values()[1:])  # skip header
    
    # Filter valid rows
    valid_rows: List[List[str]] = []
    for row_data in all_rows:
        if len(row_data) > 0:
            name_idx = ord(DESIGNER_COLUMNS.NAME) - ord('A')
            if name_idx < len(row_data) and str(row_data[name_idx]).strip():
                valid_rows.append([str(cell) for cell in row_data])
    
    ranked: List[Designer] = []

    for row in valid_rows:
        try:
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

            ranked.append(Designer(
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
            ))
        except Exception:
            continue

    ranked.sort(key=lambda d: -d.score)
    return [d.name for d in ranked]

def assignDesigner(pid: str) -> None:
    row = getProjectRow(pid)
    if row == -1:
        raise ValueError("Project not found")

    # check if someone is already assigned
    assign_col = ord(PROJECT_COLUMNS.ASSIGNED_DESIGNER) - ord('A') + 1
    already_assigned = frontend_project.cell(row, assign_col).value
    if already_assigned and already_assigned.strip():
        print(f"Project {formatPID(pid)} already assigned to {already_assigned}.  Skipping.")
        return

    # get priority
    priority_col = ord(PROJECT_COLUMNS.PRIORITY) - ord('A') + 1
    priority = frontend_project.cell(row, priority_col).value or "None"

    # get best designers
    designers = getBestDesigner(priority)
    chosen = designers[0] if designers else None
    if not chosen:
        print("No available designers to assign.")
        return

    # assign to sheet
    frontend_project.update_cell(row, assign_col, chosen)
    print(f"Assigned {formatPID(pid)} (priority: {priority}) to: {chosen}")

# WRITER SPECIFIC STUFF

@dataclass
class Writer:
    name:                   str
    category:               str  # STEAM topic they specialize in
    assigned_work:          List[str]
    writings_finished:      List[str]
    num_finished:           int
    quality_percent:        float
    avg_turnaround_time:    float
    kpi:                    float
    topic_rank:             int  # Ranking based on topic match
    open_tasks:             int = 0
    score:                  float = 0.0

@dataclass(frozen=True)
class WriterColumns:
    NAME: str =                 'A'
    CATEGORY: str =             'B'  # Fixed typo: CATAGORY -> CATEGORY
    ASSIGNED_WORK: str =        'C'  # list of PIDs
    WRITINGS_FINISHED: str =    'D'  # list of PIDs (changed from DESIGNS_FINISHED)
    NUM_FINISHED: str =         'E'  # count
    QUALITY_PERCENT: str =      'I'
    AVG_TURNAROUND_TIME: str =  'J'
    KPI: str =                  'K'

# Create singleton instances for use throughout the codebase
WRITER_COLUMNS = WriterColumns()

# Topic hierarchy for writer ranking (exact match gets highest priority)
TOPIC_HIERARCHY: Dict[str, int] = {
    "Science": 0,
    "Technology": 1,
    "Engineering": 2,
    "Art": 3,
    "ANY": 4,  # Can do any topic, but lower priority than specialists
    "DO NOT ASSIGN": 999  # Should never be assigned
}

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

def getBestWriter(topic: str) -> List[str]:
    """
    Returns writer names ranked best-to-worst based on KPI, topic match, and workload.
    - Sorts first by topic match, then by KPI (desc), then by workload (asc).
    """
    topic_rank: Dict[str, int] = TOPIC_HIERARCHY
    all_rows: List[List[Any]] = cast(List[List[Any]], writer_sheet.get_all_values()[1:])  # skip header
    
    # Filter valid rows
    valid_rows: List[List[str]] = []
    for row_data in all_rows:
        if len(row_data) > 0:
            name_idx = ord(WRITER_COLUMNS.NAME) - ord('A')
            if name_idx < len(row_data) and str(row_data[name_idx]).strip():
                valid_rows.append([str(cell) for cell in row_data])
    
    ranked: List[Writer] = []

    for row in valid_rows:
        try:
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

            ranked.append(Writer(
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
            ))
        except Exception:
            continue

    # Sort by score (descending)
    ranked.sort(key=lambda w: -w.score)
    return [w.name for w in ranked]

def assignWriter(pid: str, topic: str) -> None:
    """Assign the best available writer to a project based on topic."""
    row = getProjectRow(pid)
    if row == -1:
        raise ValueError("Project not found")

    # check if someone is already assigned
    assign_col = ord(PROJECT_COLUMNS.ASSIGNED_WRITER) - ord('A') + 1
    already_assigned = frontend_project.cell(row, assign_col).value
    if already_assigned and already_assigned.strip():
        print(f"Project {formatPID(pid)} already assigned to {already_assigned}. Skipping.")
        return

    # get best writers for this topic
    writers = getBestWriter(topic)
    chosen = writers[0] if writers else None
    if not chosen:
        print("No available writers to assign.")
        return

    # assign to sheet
    frontend_project.update_cell(row, assign_col, chosen)
    print(f"Assigned {formatPID(pid)} (topic: {topic}) to writer: {chosen}")

def notifyDesigner(designer: str) -> bool:
    
    
if __name__ == "__main__":
    # Example usage
    try:
        # Assign a writer for a Science topic
        assignWriter("000001", "Science")
        
        # Assign a designer with high priority
        assignDesigner("000001")
        
        # Test writer ranking for different topics
        print("Best writers for Science:", getBestWriter("Science")[:3])
        print("Best writers for Technology:", getBestWriter("Technology")[:3])
        print("Best writers for Art:", getBestWriter("Art")[:3])
        
    except Exception as e:
        print(f"Error in assignment: {e}")