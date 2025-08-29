import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# CONFIG - Now using environment variables
FRONTEND_SHEET = os.getenv('PROJECT_SHEET_ID', "STEAMXchange frontend management system")
MANAGEMENT_SHEET = os.getenv('MANAGEMENT_SHEET_ID', "STEAMXChange Management")
CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', "steamxquality-d4784ddb6b40.json")

# AUTH
scope: list[str] = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope) # type: ignore
client = gspread.authorize(creds) # type: ignore

# SHEETS
frontend_sheet: gspread.Spreadsheet = client.open_by_key(FRONTEND_SHEET)
frontend_project: gspread.Worksheet = frontend_sheet.worksheet("Projects")

management_sheet: gspread.Spreadsheet = client.open_by_key(MANAGEMENT_SHEET)
contact_sheet: gspread.Worksheet = management_sheet.worksheet("Contact Directory")

# Column mappings for the Projects sheet
PROJECT_COLUMNS = {
    # INFO
    'PROJECT_ID':            'D',
    'PROJECT_NAME':          'E',
    'DESCRIPTION':           'F',
    'PRIORITY':              'G',
    'WRITER_REQUIRED':       'H',  # was "WRITER?"
    'DESIGNER_REQUIRED':     'I',  # was "DESIGNER?"
    'READY_TO_ASSIGN':       'J',

    # WRITERS
    'ASSIGNED_WRITER':       'K',
    'DOCUMENT_LINK':         'L',
    'WRITER_DEADLINE':       'M',
    'WRITER_SEND_METHOD':    'N',

    # WRITER QC
    'WRITER_QC_CONTROLLER':  'O',
    'WRITER_QC_FORM_POST':   'P',
    'WRITER_REVISION_COUNT': 'Q',
    'WRITER_QC_RESULT':      'R',

    # DESIGNERS
    'ASSIGNED_DESIGNER':     'S',
    'MEDIA_LINK':            'T',
    'DESIGN_DEADLINE':       'U',
    'DESIGN_SEND_METHOD':    'V',

    # DESIGNER QC
    'DESIGN_QC_CONTROLLER':  'W',
    'DESIGN_QC_FORM_POST':   'X',
    'DESIGN_REVISION_COUNT': 'Y',
    'DESIGN_QC_RESULT':      'Z',
}

def formatPID(pid: str | int) -> str:
    """
    Formats your PID so it can work with other functions.
    """
    # normalize to int first
    if isinstance(pid, str):
        # strip any leading '#' and whitespace
        pid = pid.strip().lstrip("#")
    try:
        num = int(pid)
    except ValueError:
        raise ValueError(f"Invalid project ID: {pid}")

    if num < 0 or num > 999999:
        raise ValueError("Project ID must be between 0 and 999999")

    return f"#{num:06d}"

def getProjectRow(project_id: str) -> int:
    """
    Return 1-based row of the given PID in column A, or -1 if not found.
    Always coerces values to string before strip/lstrip.
    """
    # normalize input
    pid = str(project_id).strip().lstrip("'")
    if not pid.startswith("#") and pid.isdigit():
        pid = formatPID(pid)  # from earlier

    col_vals = frontend_project.col_values(1)  # column A

    for row_num, val in enumerate(col_vals[2:], start=3):  # skip 2 header rows
        cell_pid = str(val).strip().lstrip("'")
        if cell_pid == pid:
            return row_num

    return -1
    
if __name__ == "__main__":
    print(getProjectRow("1"))