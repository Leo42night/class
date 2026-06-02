from google.oauth2.credentials import Credentials as Cred_Auth
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import os

# =========================
# SCOPES
# =========================
AUTH_SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.students.readonly",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.profile.emails",
    "https://www.googleapis.com/auth/classroom.profile.photos",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/admin.reports.audit.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

TOKEN_FILE = "token_auth.json"
CLIENT_SECRET_FILE = "credentials.json"
REPO_PATH = "C:/Users/karma/repo"

# =========================
# CORE OAUTH CREDS
# =========================
def _get_auth_creds():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Cred_Auth.from_authorized_user_file(TOKEN_FILE, AUTH_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                AUTH_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


# =========================
# GOOGLE SERVICES
# =========================

def get_service_sheets():
    return build("sheets", "v4", credentials=_get_auth_creds())


def get_service_courses():
    return build("classroom", "v1", credentials=_get_auth_creds())


def get_service_drive():
    return build("drive", "v3", credentials=_get_auth_creds())


def get_service_admin():
    return build("admin", "reports_v1", credentials=_get_auth_creds())