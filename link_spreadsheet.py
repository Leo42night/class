# tambahkan link ke nama repo

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "service-account.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("sheets", "v4", credentials=creds)

SPREADSHEET_ID = "REMOVED_SECRET"

# ambil sheetId dari sheet "temporal"
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()

sheet_id = None
for s in spreadsheet["sheets"]:
    if s["properties"]["title"] == "temporal":
        sheet_id = s["properties"]["sheetId"]

request = {
    "requests": [
        {
            "updateCells": {
                "start": {
                    "sheetId": sheet_id,
                    "rowIndex": 2,
                    "columnIndex": 5
                },
                "rows": [
                    {
                        "values": [
                            {
                                "userEnteredValue": {
                                    "stringValue": "Repository"
                                },
                                "textFormatRuns": [
                                    {
                                        "startIndex": 0,
                                        "format": {
                                            "link": {
                                                "uri": "https://github.com/user/repo"
                                            },
                                            "underline": True,
                                            "foregroundColor": {
                                                "red": 0,
                                                "green": 0,
                                                "blue": 1
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "fields": "userEnteredValue,textFormatRuns"
            }
        }
    ]
}


service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body=request
).execute()

print("Link berhasil dibuat")