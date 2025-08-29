from dataclasses import dataclass
from typing import List, Dict, Union, Any, cast
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

# Column mappings for the Projects sheet
PROJECT_COLUMNS: Dict[str, str] = {
    # INFO
    'PROJECT_ID':            'A',
    'PROJECT_NAME':          'B',
    'DESCRIPTION':           'C',
    'PRIORITY':              'D',
    'WRITER_REQUIRED':       'E',  # was "WRITER?"
    'DESIGNER_REQUIRED':     'F',  # was "DESIGNER?"
    'READY_TO_ASSIGN':       'G',

    # WRITERS
    'ASSIGNED_WRITER':       'I',
    'DOCUMENT_LINK':         'J',
    'WRITER_DEADLINE':       'K',
    'WRITER_SEND_METHOD':    'L',

    # WRITER QC
    'WRITER_QC_CONTROLLER':  'N',
    'WRITER_QC_FORM_POST':   'O',
    'WRITER_REVISION_COUNT': 'P',
    'WRITER_QC_RESULT':      'Q',

    # DESIGNERS
    'ASSIGNED_DESIGNER':     'S',
    'MEDIA_LINK':            'T',
    'DESIGN_DEADLINE':       'U',
    'DESIGN_SEND_METHOD':    'V',

    # DESIGNER QC
    'DESIGN_QC_CONTROLLER':  'X',
    'DESIGN_QC_FORM_POST':   'Y',
    'DESIGN_REVISION_COUNT': 'Z',
    'DESIGN_QC_RESULT':      'AA',
}

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
    name: str
    platform: str
    assigned_work: list[str]
    designs_finished: list[str]
    num_finished: int
    quality_percent: float
    avg_turnaround_time: float
    kpi: float
    platform_rank: int
    open_tasks: int = 0
    score: float = 0.0

DESIGNER_COLUMNS: Dict[str, str] = {
    'NAME':                 'A',
    'PLATFORM':             'B',
    'ASSIGNED_WORK':        'C',  # list of PIDs
    'DESIGNS_FINISHED':     'D',  # list of PIDs
    'NUM_FINISHED':         'E',  # count
    'QUALITY_PERCENT' :     'I',
    'AVG_TURNAROUND_TIME':  'J',
    'KPI':                  'K'
}

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
    platform_rank: dict[str, int] = {p: i for i, p in enumerate(PLATFORM_HIERARCHY)}
    rows = [
        row for row in designer_sheet.get_all_values()[1:]
        if len(row) > 0 and row[ord(DESIGNER_COLUMNS['NAME']) - ord('A')].strip()
    ]
    ranked: List[Designer] = []

    for row in rows:
        try:
            def get(col: str) -> str:
                idx = ord(DESIGNER_COLUMNS[col]) - ord('A')
                return row[idx].strip() if idx < len(row) else ""

            name = get('NAME')
            platform = get('PLATFORM')
            kpi = float(get('KPI') or 0)

            assigned_work = [pid.strip() for pid in get('ASSIGNED_WORK').split(',') if pid.strip()]
            finished_work = [pid.strip() for pid in get('DESIGNS_FINISHED').split(',') if pid.strip()]
            open_tasks = len(set(assigned_work) - set(finished_work))

            platform_bonus = max(0, 5 - platform_rank.get(platform, len(PLATFORM_HIERARCHY)))
            workload_penalty = getWorkloadPenalty(priority, open_tasks)
            score = kpi + platform_bonus - workload_penalty

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
    assign_col = ord(PROJECT_COLUMNS['ASSIGNED_DESIGNER']) - ord('A') + 1
    already_assigned = frontend_project.cell(row, assign_col).value
    if already_assigned and already_assigned.strip():
        print(f"Project {formatPID(pid)} already assigned to {already_assigned}.  Skipping.")
        return

    # get priority
    priority_col = ord(PROJECT_COLUMNS['PRIORITY']) - ord('A') + 1
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



if __name__ == "__main__":
    print(assignDesigner("2"))