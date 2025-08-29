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


def getProjectRow(projectID: str) -> int:
    try:
        # Get all values in the PROJECT_ID column
        project_ids = frontend_project.col_values(gspread.utils.a1_to_rowcol(PROJECT_COLUMNS['PROJECT_ID'] + '1')[1])
        
        # Find the row with matching project ID
        for i, cell_value in enumerate(project_ids):
            if cell_value == projectID:
                return i + 1  # +1 because gspread uses 1-based indexing
        
        # Return -1 if project ID not found
        return -1
        
    except Exception as e:
        print(f"Error finding project row: {e}")
        return -1