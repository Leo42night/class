# -- main import (Credential Classroom, Credential Spreadsheet)--
from google.oauth2.credentials import Credentials as Cred_Auth
from google.oauth2.service_account import Credentials as Cred_Serv
from googleapiclient.discovery import build

## --- CLASSROOOM ---
# ambil credential berdasarkan auth credentials.json (API & Services -> Credentials)
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

AUTH_SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.student-submissions.students.readonly",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/classroom.profile.emails",
    "https://www.googleapis.com/auth/classroom.profile.photos",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/admin.reports.audit.readonly"
]


def _get_auth_creds():
    """Shared OAuth creds untuk Classroom & Drive."""
    creds = None

    if os.path.exists("token_auth.json"):
        creds = Cred_Auth.from_authorized_user_file("token_auth.json", AUTH_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", AUTH_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token_auth.json", "w") as token:
            token.write(creds.to_json())

    return creds


## --- SPREADSHEET ---
# ambil credential berdasarkan service-account.json (IAM -> Service Account)

SERVICE_ACCOUNT_FILE = "service-account.json"
SERV_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
REPO_PATH = "C:/Users/karma/repo"


def get_service_sheets():
    creds = Cred_Serv.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SERV_SCOPES
    )
    service = build("sheets", "v4", credentials=creds)
    return service

def get_service_courses():
    return build("classroom", "v1", credentials=_get_auth_creds())


def get_service_drive():
    return build("drive", "v3", credentials=_get_auth_creds())

def get_service_admin():
    return build("admin", "reports_v1", credentials=_get_auth_creds())