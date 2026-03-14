from auth import get_service
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd

service_classroom = get_service()

# Spreadsheet config
SPREADSHEET_ID = "REMOVED_SECRET"
SERVICE_ACCOUNT_FILE = "service-account.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

sheets = build("sheets", "v4", credentials=creds)

# =============================
# Ambil data dari Google Classroom
# =============================

course_id = "825266594962"
coursework_id = "846975898465"

submissions = service_classroom.courses().courseWork().studentSubmissions().list(
    courseId=course_id,
    courseWorkId=coursework_id
).execute()

github_map = {}

for sub in submissions.get("studentSubmissions", []):
    user_id = sub["userId"]

    student = service_classroom.courses().students().get(
        courseId=course_id,
        userId=user_id
    ).execute()

    name = student["profile"]["name"]["fullName"]

    attachments = sub.get("assignmentSubmission", {}).get("attachments", [])

    repo = ""

    for att in attachments:
        if "link" in att:
            url = att["link"]["url"]
            if "github.com" in url:
                parts = url.replace("https://github.com/", "").replace(".git", "").split("/")
                repo = parts[0] + "/" + parts[1] if len(parts) > 1 else parts[0]
                break
            
    print(f"Memproses {name} - {repo}")

    github_map[name.casefold()] = repo

# simpan github_map ke csv
df = pd.DataFrame(github_map.items(), columns=["name", "repo"])
df.to_csv("github_map.csv", index=False)
print("github_map.csv berhasil disimpan")
exit()
# =============================
# Ambil nama dari spreadsheet
# =============================

sheet_data = sheets.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="ppwl4!B2:B37"
).execute()

names = sheet_data.get("values", [])

# =============================
# Ambil sheetId
# =============================

spreadsheet_meta = sheets.spreadsheets().get(
    spreadsheetId=SPREADSHEET_ID
).execute()

sheet_id = None

for s in spreadsheet_meta["sheets"]:
    if s["properties"]["title"] == "temporal":
        sheet_id = s["properties"]["sheetId"]

# =============================
# Buat request update
# =============================

requests = []

for i, row in enumerate(names):

    if not row:
        continue

    name = row[0]
    repo = github_map.get(name.casefold(), "")

    if not repo:
        continue

    url = f"https://github.com/{repo}"

    requests.append({
        "updateCells": {
            "start": {
                "sheetId": sheet_id,
                "rowIndex": i + 1,   # karena mulai dari B2
                "columnIndex": 2     # kolom C
            },
            "rows": [{
                "values": [{
                    "userEnteredValue": {
                        "stringValue": repo
                    },
                    "textFormatRuns": [{
                        "startIndex": 0,
                        "format": {
                            "link": {
                                "uri": url
                            },
                            "underline": True,
                            "foregroundColor": {
                                "red": 0,
                                "green": 0,
                                "blue": 1
                            }
                        }
                    }]
                }]
            }],
            "fields": "userEnteredValue,textFormatRuns"
        }
    })

# =============================
# Kirim update ke spreadsheet
# =============================

if requests:
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": requests}
    ).execute()

print("Update selesai.")