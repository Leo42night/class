# masukkan email dari course data students -> sheet main column email
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(__file__))
)  # agar import env dapat diakses
from config.env import env
from config.cred import get_service_sheets, get_service_courses

TAB = "Nilai"
START_ROW = 3
NAME_COL = "B"
EMAIL_COL = "U"


def get_course_by_code(code):  # 'a' or 'b' -> cid, course_name

    cid = env.COURSE_ID_B if code == "b" else env.COURSE_ID_A
    return cid, f"Praktikum PWL 2026 [{code.upper()}]"

if __name__ == "__main__":
    print("Course Gmail into sheet : default kelas: a, opsi -> 'a' atau 'b'")
    code = sys.argv[1] if len(sys.argv) >= 2 else "a"
    small_code = code.lower()
    course_id, course_name = get_course_by_code(small_code)
    cnf = env.get_config(small_code)
    SPREADSHEET_ID = cnf["spreadsheet"]
    N_STUDENT = cnf["n_student"]
    print(f"{course_name} | [{SPREADSHEET_ID}] | {N_STUDENT} students")

    service_courses = get_service_courses()
    service_sheet = get_service_sheets()

    # 1. Ambil daftar siswa dari Google Classroom
    print("Mengambil data siswa dari Classroom...")
    results = service_courses.courses().students().list(courseId=course_id).execute()
    students_classroom = results.get("students", [])

    # Mapping { "nama_lower": {"full_name": "Asli", "email": "..."} }
    # Kita simpan objek agar bisa melacak mana yang sudah dipasangkan
    email_map = {
        s["profile"]["name"]["fullName"].lower(): {
            "email": s["profile"]["emailAddress"],
            "full_name": s["profile"]["name"]["fullName"],
            "used": False,  # Flag untuk menandai apakah sudah masuk ke sheet
        }
        for s in students_classroom
    }

    # 2. Ambil daftar nama dari Spreadsheet
    range_names = f"{TAB}!{NAME_COL}{START_ROW}:{NAME_COL}{START_ROW + N_STUDENT - 1}"
    sheet_data = (
        service_sheet.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=range_names)
        .execute()
    )

    names_in_sheet = sheet_data.get("values", [])

    # 3. Proses Pencocokan
    emails_to_update = []
    failed_in_sheet = []

    for index, row in enumerate(names_in_sheet):
        if not row or not row[0].strip():
            emails_to_update.append([""])
            continue

        name_from_sheet = row[0].strip()
        name_lower = name_from_sheet.lower()

        if name_lower in email_map:
            emails_to_update.append([email_map[name_lower]["email"]])
            email_map[name_lower]["used"] = True  # Tandai sudah ada pasangannya
        else:
            emails_to_update.append([""])
            failed_in_sheet.append(f"Baris {START_ROW + index}: {name_from_sheet}")

    # 4. Tulis ke Spreadsheet
    update_range = f"{TAB}!{EMAIL_COL}{START_ROW}"
    service_sheet.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption="USER_ENTERED",
        body={"values": emails_to_update},
    ).execute()

    # 5. Tampilkan Laporan Ke Console
    print("\n" + "=" * 50)

    # A. Nama di Sheet tapi TIDAK ADA di Classroom
    if failed_in_sheet:
        print(f"❌ {len(failed_in_sheet)} NAMA DI SHEET TIDAK DITEMUKAN DI CLASSROOM:")
        for entry in failed_in_sheet:
            print(f"   - {entry}")
    else:
        print("✅ Semua nama di Sheet memiliki pasangan di Classroom.")

    print("-" * 50)

    # B. Siswa di Classroom tapi TIDAK ADA di Sheet (Yatim Piatu)
    unpaired_classroom = [info for info in email_map.values() if not info["used"]]

    if unpaired_classroom:
        print(
            f"⚠️  {len(unpaired_classroom)} SISWA CLASSROOM TIDAK ADA DI DAFTAR SHEET:"
        )
        for student in unpaired_classroom:
            print(f"   - {student['full_name']} ({student['email']})")
    else:
        print("✅ Tidak ada siswa tambahan di Classroom.")

    print("=" * 50)
