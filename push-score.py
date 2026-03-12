import re
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = "REMOVED_SECRET"
SERVICE_ACCOUNT_FILE = "service-account.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("sheets", "v4", credentials=creds)

# =========================
# PARSE FILE TXT
# =========================

# load nama
with open("names-a.txt", encoding="utf-8") as f:
    names = [n.strip().casefold() for n in f if n.strip()]

students = {n: {"notes": [], "minus": 0} for n in names}

current_name = None

with open("ppwl5-a-submisi.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()

        # jika menemukan "> nama"
        if line.startswith(">"):
            name = line[1:].strip().casefold()

            if name in students:
                current_name = name
            else:
                current_name = None

            continue

        # stop jika baris kosong
        if line == "":
            current_name = None
            continue

        # ambil note
        if current_name and line.startswith("-"):
            students[current_name]["notes"].append(line)

            m = re.match(r"-([0-9]+)", line)
            if m:
                students[current_name]["minus"] += int(m.group(1))

# hitung score
for name in students:
    students[name]["score"] = 100 - students[name]["minus"]

# =========================
# HITUNG NILAI
# =========================

for s in students:
    print(s, students[s])
    students[s]["score"] = 100 - students[s]["minus"]
# exit()
# =========================
# AMBIL NAMA DARI SHEET
# =========================

sheet_data = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="ppwl5!B2:B23"
).execute()
print("\nsheet_data: ", sheet_data)

names = sheet_data.get("values", [])

updates = []

for i, row in enumerate(names):

    if not row:
        continue

    name = row[0]
    key = name.casefold()

    if key not in students:
        continue

    notes = "\n".join(students[key]["notes"])
    score = students[key]["score"]
    # print(f"{name}, {notes}, {score}")
    updates.append({
        "range": f"ppwl5!D{i+2}:E{i+2}",
        "values": [[notes, score]]
    })

# =========================
# UPDATE SHEET
# =========================

body = {
    "valueInputOption": "USER_ENTERED",
    "data": updates
}

service.spreadsheets().values().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body=body
).execute()

print("Nilai berhasil dimasukkan.")