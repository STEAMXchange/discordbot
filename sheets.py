from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# CONFIG
PROJECT_SHEET = os.getenv("PROJECT_SHEET_NAME", "STEAMXchange frontend management system")
PROJECT_TAB = os.getenv("PROJECT_SHEET_TAB", "Projects")
MANAGEMENT_SHEET = os.getenv("MANAGEMENT_SHEET_NAME", "STEAMXChange Management")
MANAGEMENT_TAB = os.getenv("MANAGEMENT_SHEET_TAB", "Contact Directory")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "steamxquality-d4784ddb6b40.json")

# AUTH
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

# SHEETS
project_sheet = client.open(PROJECT_SHEET).worksheet(PROJECT_TAB)
management_sheet = client.open(MANAGEMENT_SHEET).worksheet(MANAGEMENT_TAB)

projects = project_sheet.get_all_records(head=2)
management_data = management_sheet.get_all_values()


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
    return _getProjectRow(project_id.zfill(6)) is not None

def markDesignerDone(project_id, design_link=None, qc_post_link=None):
    for i, row in enumerate(projects, start=3):  # adjust for headers
        if str(row["PROJECT ID"]).lstrip("#") == project_id:
            if design_link:
                project_sheet.update(f"N{i}", [[design_link]])
            else:
                project_sheet.update(f"N{i}", [["IMAGE SENT IN QC CHAT"]])
            project_sheet.update(f"O{i}", [[datetime.today().strftime("%B %d, %Y")]])
            if qc_post_link:
                project_sheet.update(f"Q{i}", [[qc_post_link]])
            project_sheet.update(f"R{i}", [["REVIEWING"]])
            return True
    return False

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

def _getProjectRow(project_id):
    project_id = str(project_id).zfill(6)  # normalize to 6-digit string
    return next((row for row in projects if str(row["PROJECT ID"]).lstrip("#").zfill(6) == project_id), None)

def markQCResult(project_id, status, reason=None):
    projects = project_sheet.get_all_records(head=2)  # refresh

    for i, row in enumerate(projects, start=3):
        if str(row["PROJECT ID"]).lstrip("#") == project_id:
            project_sheet.update(f"R{i}", [[status.upper()]])
            if status.upper() == "FAIL":
                if not reason:
                    print("[ERROR] Fail reason missing!")
                    return False
                project_sheet.update(f"S{i}", [[reason]])
            else:
                project_sheet.update(f"S{i}", [[""]])  # clear fail reason
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
