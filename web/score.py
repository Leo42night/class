# Rutin: fetch users, lalu match by email ke sheet, dan update kolom score. 
# Tujuannya agar bisa lihat progress di sheet, tanpa harus cek satu-satu di web.
# !! Pastikan kolom score di sheet di ubah tiap fase
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(__file__))
)  # agar import env dapat diakses
from config.env import env
from config.cred import get_service_sheets, get_service_courses
import requests

# BASE_URL = "http://localhost:3000"
BASE_URL = "https://ppwl-be.vercel.app"
KEY = "learn"
HEADERS = {
    "Content-Type": "application/json",
}

TAB = "Nilai"
START_ROW = 3
EMAIL_COL = "U"
SCORE_COL = "Z" # fase 1: W, fase 2: Z, fase 3: AC, fase 4: AF


def get_course_by_code(code):  # 'a' or 'b' -> cid, course_name
    cid = env.COURSE_ID_B if code == "b" else env.COURSE_ID_A
    return cid, f"Praktikum PWL 2026 [{code.upper()}]"


def get_top_users():
    url = f"{BASE_URL}/api/users"
    params = {"key": KEY}

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()

        users = response.json()

        achievers = [
            user for user in users if user.get("score", 0) >= user.get("score_max", 0)
        ]

        if achievers:
            print(f"--- Users yang Mencapai/Melebihi Target ({len(achievers)}) ---")
            for user in achievers:
                name = user.get("name", "Unknown")
                score = user.get("score")
                target = user.get("score_max")
                print(f"User: {name} | Score: {score} | Max: {target}")

            total_users = len(users)
            total_achievers = len(achievers)
            print(f"Persentase: {total_achievers / total_users * 100:.2f}%")
        else:
            print("Tidak ada user yang memenuhi kriteria.")

        return users  # kembalikan semua user untuk keperluan update sheet

    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan saat mengambil data: {e}")
        return []


def build_email_score_map(users):
    """Buat dict {email: score} dari list user."""
    return {
        user["email"]: user.get("score", 0)
        for user in users
        if "email" in user
    }


def read_sheet_emails(service_sheet, spreadsheet_id, n_student):
    """
    Baca kolom EMAIL_COL dari sheet TAB mulai START_ROW.
    Return list of (row_index, email) — row_index adalah nomor baris di sheet (1-based).
    """
    end_row = START_ROW + n_student - 1
    range_notation = f"{TAB}!{EMAIL_COL}{START_ROW}:{EMAIL_COL}{end_row}"

    result = (
        service_sheet.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_notation)
        .execute()
    )

    rows = result.get("values", [])
    email_rows = []
    for i, row in enumerate(rows):
        actual_row = START_ROW + i
        email = row[0].strip() if row else ""
        email_rows.append((actual_row, email))

    return email_rows


def update_scores_to_sheet(service_sheet, spreadsheet_id, email_rows, email_score_map):
    """
    Untuk setiap baris di sheet, cari email di email_score_map,
    lalu tulis score ke SCORE_COL pada baris yang sama.
    Menggunakan batch update agar lebih efisien.
    """
    data = []
    matched = 0
    not_found = []

    for row_num, email in email_rows:
        if not email:
            continue

        if email in email_score_map:
            score = email_score_map[email]
            range_notation = f"{TAB}!{SCORE_COL}{row_num}"
            data.append({
                "range": range_notation,
                "values": [[score]],
            })
            matched += 1
        else:
            not_found.append(email)

    if not data:
        print("Tidak ada data yang cocok untuk diupdate.")
        return

    body = {
        "valueInputOption": "USER_ENTERED",  # agar angka tidak dianggap string
        "data": data,
    }

    result = (
        service_sheet.spreadsheets()
        .values()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )

    updated_cells = result.get("totalUpdatedCells", 0)
    print("\n--- Update Sheet Selesai ---")
    print(f"Matched & updated : {matched} baris ({updated_cells} sel)")
    print(f"Email tidak ditemukan di API: {len(not_found)}")
    if not_found:
        for e in not_found:
            print(f"  - {e}")


if __name__ == "__main__":
    print("Web Score -> Sheet: default kelas: a, opsi -> 'a' atau 'b'")
    code = sys.argv[1] if len(sys.argv) >= 2 else "a"
    small_code = code.lower()
    course_id, course_name = get_course_by_code(small_code)
    cnf = env.get_config(small_code)
    SPREADSHEET_ID = cnf["spreadsheet"]
    N_STUDENT = cnf["n_student"]
    print(f"{course_name} | [{SPREADSHEET_ID}] | {N_STUDENT} students")

    service_courses = get_service_courses()
    service_sheet = get_service_sheets()

    # 1. Ambil semua user dari API
    users = get_top_users()
    if not users:
        print("Tidak ada user dari API, proses dihentikan.")
        sys.exit(1)

    # 2. Bangun map email -> score
    email_score_map = build_email_score_map(users)
    print(f"\nTotal user dengan email: {len(email_score_map)}")

    # 3. Baca daftar email dari sheet
    print(f"Membaca email dari sheet '{TAB}' kolom {EMAIL_COL} ...")
    email_rows = read_sheet_emails(service_sheet, SPREADSHEET_ID, N_STUDENT)
    print(f"Ditemukan {len(email_rows)} baris di sheet.")
    
    confirm = input(f"\nUpdate ke '{TAB}'? (y/n) >> ").strip().lower()
    if confirm != "y":
        print("⏭️  Dilewati.")
        sys.exit(0)

    # 4. Update score ke sheet berdasarkan kecocokan email
    update_scores_to_sheet(service_sheet, SPREADSHEET_ID, email_rows, email_score_map)