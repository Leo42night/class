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
]


def get_service_courses():
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

    service = build("classroom", "v1", credentials=creds)
    return service


## --- SPREADSHEET ---
# ambil credential berdasarkan service-account.json (IAM -> Service Account)

SERVICE_ACCOUNT_FILE = "service-account.json"
SERV_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_service_sheets():
    creds = Cred_Serv.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SERV_SCOPES
    )
    service = build("sheets", "v4", credentials=creds)
    return service
