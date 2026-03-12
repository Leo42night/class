# templating score dari txt ke spreadsheet & classroom

import re
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "service-account.json"

# PPWL-A =========================
name_class = "ppwl-a"
SPREADSHEET_ID = "REMOVED_SECRET"
course_id = "825125683344"
coursework_id = "847559064760"


# PPWL-B =========================
# name_class = "ppwl-b"
# SPREADSHEET_ID = ""
# course_id = "825266594962"
# coursework_id = ""

# Assignment
tugas_ke = 5
range_sheet = "ppwl5!B2:B23"

creds_sheet = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

service_sheet = build("sheets", "v4", credentials=creds_sheet)

# =========================
# PARSE FILE TXT
# =========================

# load nama
with open(f"{name_class}-names.txt", encoding="utf-8") as f:
    names = [n.strip().casefold() for n in f if n.strip()]

students = {n: {"notes": [], "minus": 0} for n in names}

current_name = None

with open(f"{name_class}-{tugas_ke}-score.txt", "r", encoding="utf-8") as f:
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
    students[s]["score"] = 100 - students[s]["minus"]
# exit()

# =========================
# AMBIL NAMA DARI SHEET
# =========================

sheet_data = service_sheet.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=range_sheet
).execute()
print("\n Sheet Key Loaded: ", sheet_data)

names = sheet_data.get("values", [])

# for spreadsheet
updates = []

# for UI: List untuk menampung data tampilan tabel
table_data = []

for i, row in enumerate(names):
    if not row:
        continue

    name = row[0]
    key = name.casefold()

    if key not in students:
        continue

    student_info = students[key]
    score = student_info["score"]
    # Gabungkan notes, ganti baris baru dengan koma agar tetap satu baris di tabel terminal
    notes_display = ", ".join(student_info["notes"])
    notes_raw = "\n".join(student_info["notes"])
    
    updates.append({
        "range": f"ppwl{tugas_ke}!D{i+2}:E{i+2}",
        "values": [[notes_raw, score]]
    })

    table_data.append({
        "row": i + 2,
        "name": name,
        "notes": notes_display,
        "score": score
    })

# --- PRINT DALAM BENTUK TABEL ---
if table_data:
    # Definisi lebar kolom: Row(6), Name(25), Notes(40), Score(6)
    template = "{:<5} | {:<25} | {:<40} | {:<6}"
    header = template.format("Row", "Name", "Notes Summary", "Score")
    separator = "-" * len(header)
    
    print("\n" + separator)
    print(header)
    print(separator)
    
    for item in table_data:
        # Potong notes jika terlalu panjang (>37 karakter) agar tabel tetap rapi
        display_note = (item['notes'][:37] + '..') if len(item['notes']) > 37 else item['notes']
        
        print(template.format(
            item['row'], 
            item['name'][:25], 
            display_note, 
            item['score']
        ))
    
    print(separator)
    print(f"Total: {len(table_data)} data siap di-update.\n")
else:
    print("⚠️ Tidak ada data siswa yang cocok ditemukan.")
# exit()
# =========================
# UPDATE SHEET
# =========================

body = {
    "valueInputOption": "USER_ENTERED",
    "data": updates
}

# service_sheet.spreadsheets().values().batchUpdate(
#     spreadsheetId=SPREADSHEET_ID,
#     body=body
# ).execute()

print(f"✅ Nilai berhasil dimasukkan ke GoogleSheet {name_class}.")

# =========================
# UPDATE SCORE IN CLASSROOM SUBMISSION
# =========================
from auth import get_service

print("Konfigurasi Classroom...")
service = get_service()

coursework_id2 = "851359030534"
submissions = service.courses().courseWork().studentSubmissions().list(
    courseId=course_id,
    courseWorkId=coursework_id2
).execute()

print(f"Submit {len(submissions.get('studentSubmissions', []))} score ke Classroom...")
# exit()

for sub in submissions.get("studentSubmissions", []):
    user_id = sub["userId"]
    submission_id = sub["id"]

    student = service.courses().students().get(
        courseId=course_id,
        userId=user_id
    ).execute()

    name = student["profile"]["name"]["fullName"].casefold()

    if name not in students:
        continue

    score = students[name]["score"]

    print(f"Update nilai {name} -> {score}, {submission_id}")

    # update nilai (draft)
    service.courses().courseWork().studentSubmissions().patch(
        courseId=course_id,
        courseWorkId=coursework_id2,
        id=submission_id,
        updateMask="assignedGrade,draftGrade", 
        body={
            "assignedGrade": score,
            "draftGrade": score
        }
    ).execute()

print("✅ Nilai berhasil dimasukkan ke Classroom")