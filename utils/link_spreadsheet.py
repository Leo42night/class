# tambahkan link github repo di spreadsheet untuk value cell <username>/<repo>
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(__file__))
)  # agar import env dapat diakses
from config.env import env
from config.cred import service

SPREADSHEET_ID = env.SPREADSHEET_ID_A
TAB = "Nilai"
RANGE = f"{TAB}!C3:C38"

sheet = service.spreadsheets()

# ambil sheet id
spreadsheet = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_id = 0
for s in spreadsheet["sheets"]:
    if s["properties"]["title"] == TAB:
        sheet_id = s["properties"]["sheetId"]
    print(s["properties"]["title"], s["properties"]["sheetId"])

# ambil username
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()

values = result.get("values", [])

requests = []

start_row = 2  # karena C3 → index row 2 (0-based)
col_index = 2  # column C

for i, row in enumerate(values):
    username = row[0].strip()
    github_link = f"https://github.com/{username}"

    requests.append(
        {
            "updateCells": {
                "rows": [
                    {
                        "values": [
                            {
                                "userEnteredValue": {"stringValue": username},
                                "textFormatRuns": [
                                    {
                                        "startIndex": 0,
                                        "format": {
                                            "link": {"uri": github_link},
                                            "underline": True,
                                            "foregroundColor": {
                                                "red": 0,
                                                "green": 0,
                                                "blue": 1,
                                            },
                                        },
                                    }
                                ],
                            }
                        ]
                    }
                ],
                "fields": "userEnteredValue,textFormatRuns",
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row + i,
                    "endRowIndex": start_row + i + 1,
                    "startColumnIndex": col_index,
                    "endColumnIndex": col_index + 1,
                },
            }
        }
    )

body = {"requests": requests}

sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

print("Hyperlink GitHub berhasil ditambahkan.")
