from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# CONFIG - Now using environment variables
PROJECT_SHEET = os.getenv('PROJECT_SHEET_NAME', "STEAMXchange frontend management system")
PROJECT_TAB = os.getenv('PROJECT_SHEET_TAB', "Projects")
MANAGEMENT_SHEET = os.getenv('MANAGEMENT_SHEET_NAME', "STEAMXChange Management")
MANAGEMENT_TAB = os.getenv('MANAGEMENT_SHEET_TAB', "Contact Directory")
CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', "steamxquality-d4784ddb6b40.json")

# AUTH
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

# SHEETS
project_sheet = client.open(PROJECT_SHEET).worksheet(PROJECT_TAB)
management_sheet = client.open(MANAGEMENT_SHEET).worksheet(MANAGEMENT_TAB)

projects = project_sheet.get_all_records(head=2)
management_data = management_sheet.get_all_values()

class ProjectCols:
    ID = "PROJECT ID"
    DONE = "PROJECT DONE?"
    START_DATE = "START DATE"
    END_DATE = "END DATE"
    DURATION = "DURATION"
    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"
    TOPIC = "TOPIC"
    AUTHOR = "ASSIGNED AUTHOR"
    AUTHOR_FILE = "LINK TO FILE"
    AUTHOR_DUE = "WRITER DUE DATE"
    DESIGNER = "ASSIGNED DESIGNER"
    DESIGN_LINK = "DESIGN LINK"
    DESIGNER_DUE = "DESIGNER DUE DATE"
    QC_POST = "QC POST"
    QC_PASSED = "QC PASSED?"
    QC_FAIL_REASON = "FAIL REASON"
    REVISION_COUNT = "# REVISIONS"
    QUALITY_CONTROLLER = "QUALITY CONTROLLER"
    QC_EXIT_DATE = "QC EXIT DATE"
    READY_TO_POST = "READY TO BE POSTED?"
    POSTER = "POSTER NAME"

def getProjectValue(project_id, col):
    row = getProjectRow(project_id)
    if not row:
        return None
    return row.get(col, None)

def getProjectRow(project_id):
    """Returns just the row dict for a project."""
    return _getProjectRow(project_id)

def getProjectRowWithIndex(project_id):
    """Returns (row_dict, row_index) where row_index is 1-based for Google Sheets."""
    project_id = str(project_id).zfill(6)
    for i, row in enumerate(projects, start=3):  # head=2 so data starts at row 3
        if str(row["PROJECT ID"]).lstrip("#").zfill(6) == project_id:
            return row, i
    return None, None


def getDesignerFromProjectID(project_id):
    row = _getProjectRow(project_id)
    return row["ASSIGNED DESIGNER"].strip() if row else None

def isProjectDone(project_id):
    row = _getProjectRow(project_id)
    if not row:
        return False
    status = str(row.get("PROJECT DONE?", "")).strip().upper()
    return status == "DONE"

def getWriterFromProjectID(project_id):
    row = _getProjectRow(project_id)
    return row["ASSIGNED AUTHOR"].strip() if row else None

def getDepartmentFromDiscord(discord_username):
    for row in management_data[2:]:
        for dept, (name_col, username_col) in {
            "Writers": (0, 1),
            "Designers": (4, 5),
            "Quality Control": (8, 9),
            "Management": (12, 14),
        }.items():
            try:
                if row[username_col].strip().lower() == discord_username.lower():
                    return dept
            except IndexError:
                continue
    return None


def getDepartmentFromName(real_name):
    for row in management_data[2:]:
        for dept, (name_col, _) in {
            "Writers": (0, 1),
            "Designers": (4, 5),
            "Quality Control": (8, 9),
            "Management": (12, 14),
        }.items():
            try:
                if row[name_col].strip().lower() == real_name.lower():
                    return dept
            except IndexError:
                continue
    return None


def getDiscordUsername(real_name):
    if not real_name:
        return None
    for row in management_data[2:]:
        for name_col, username_col in [(0, 1), (4, 5), (8, 9), (12, 14)]:
            try:
                name = row[name_col].strip()
                user = row[username_col].strip()
                if name.lower() == real_name.lower():
                    return user
            except IndexError:
                continue
    return None

def projectExists(project_id):
    return _getProjectRow(project_id) is not None

def markDesignerDone(project_id, design_link=None, qc_post_link=None):
    for i, row in enumerate(projects, start=3):  # adjust for headers
        if str(row["PROJECT ID"]).lstrip("#") == project_id:
            if design_link:
                project_sheet.update(f"O{i}", [[design_link]])
            else:
                project_sheet.update(f"O{i}", [["IMAGE SENT IN QC CHAT"]])
            project_sheet.update(f"P{i}", [[datetime.today().strftime("%B %d, %Y")]])
            if qc_post_link:
                project_sheet.update(f"R{i}", [[qc_post_link]])
            project_sheet.update(f"S{i}", [["REVIEWING"]])
            return True
    return False

def getCanvaURL(project_id):
    for i, row in enumerate(projects, start=3):  # adjust for headers
        if str(row["PROJECT ID"]).lstrip("#") == project_id:
            # Assuming Canva URL is in column O (same as design_link in your markDesignerDone function)
            canva_url = project_sheet.cell(i, 15).value  # Column O is 15th column
            return canva_url if canva_url else None
    return None

def getRealName(discord_username):
    for row in management_data[2:]:
        for name_col, username_col in [(0, 1), (4, 5), (8, 9), (12, 14)]:
            try:
                name = row[name_col].strip()
                user = row[username_col].strip()
                if user.lower() == discord_username.lower():
                    return name
            except IndexError:
                continue
    return None

def refresh_projects():
    global projects
    projects = project_sheet.get_all_records(head=2)

def _getProjectRow(project_id):
    project_id = str(project_id).lstrip("#").zfill(6)
    return next((row for row in projects if str(row["PROJECT ID"]).lstrip("#").zfill(6) == project_id), None)

def markQCResult(project_id, status, reason=None):
    projects = project_sheet.get_all_records(head=2)  # refresh
    project_id = str(project_id).lstrip("#").zfill(6)  # normalize input
    
    for i, row in enumerate(projects, start=3):  # data starts at row 3
        sheet_project_id = str(row["PROJECT ID"]).lstrip("#").zfill(6)
        if sheet_project_id == project_id:
            if status.upper() == "FAIL":
                if not reason:
                    print("[ERROR] Fail reason missing!")
                    return False
                project_sheet.update(f"T{i}", [[reason]])  # fail reason column
                project_sheet.update(f"S{i}", [["FAIL"]])
            else:
                project_sheet.update(f"S{i}", [[status.upper()]])
                project_sheet.update(f"T{i}", [[""]])  # clear fail reason
            return True
    return False

# TEST
if __name__ == "__main__":
    pid = input("Enter ProjectID (e.g. 000001): ").strip().lstrip("#")
    designer = getDesignerFromProjectID(pid)
    if designer:
        print(f"Designer: {designer}")
        print(f"Discord: {getDiscordUsername(designer)}")
    else:
        print("Project not found.")
