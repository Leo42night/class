# Menu Fitur Setup
# 1. Setup Spreadsheet Nama
# 2. Setup Spreadsheet Link Github Profile
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(__file__))
)  # agar import env dapat diakses

from config.cred import get_service_courses, get_service_sheets

SERVICE_ACCOUNT_FILE = "service-account.json"
TAB_NAME = "Nilai"
ROW_START = 3
NAME_COL = "B"
REPO_COL = "C"
CODENAME_COL = "T"

def _get_students(course_id: str) -> list[dict]:
    service = get_service_courses()
    students = []
    page_token = None

    while True:
        resp = (
            service.courses()
            .students()
            .list(courseId=course_id, pageToken=page_token)
            .execute()
        )

        for s in resp.get("students", []):
            students.append(
                {"name": s["profile"]["name"]["fullName"], "user_id": s["userId"]}
            )

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    students.sort(key=lambda s: s["name"])
    return students


def _get_coursework_list(course_id: str) -> list[dict]:
    service = get_service_courses()
    resp = service.courses().courseWork().list(courseId=course_id).execute()
    return resp.get("courseWork", [])


def _pick_coursework(course_id: str) -> dict | None:
    coursework = _get_coursework_list(course_id)

    if not coursework:
        print("⚠️  Tidak ada assignment di kelas ini.")
        return None

    print("\n=== Pilih Assignment ===")
    for i, w in enumerate(coursework, start=1):
        print(f"{i}. {w.get('title', 'No Title')}")
    print("0. Kembali")

    choice = input(">> ").strip()
    if choice == "0":
        return None

    try:
        return coursework[int(choice) - 1]
    except (ValueError, IndexError):
        print("Pilihan tidak valid.")
        return None


def _extract_github_username(url: str) -> str:
    parts = url.rstrip("/").replace("https://", "").replace("http://", "").split("/")
    if len(parts) >= 2:
        return parts[1]
    return url


def _get_sheet_id(service_sheet, spreadsheet_id: str, tab_name: str) -> int:
    meta = service_sheet.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets.properties"
    ).execute()
    for sheet in meta.get("sheets", []):
        if sheet["properties"]["title"] == tab_name:
            return sheet["properties"]["sheetId"]
    raise ValueError(f"Tab '{tab_name}' tidak ditemukan.")

def _fetch_codenames(service_sheet, spreadsheet_id: str, n_rows: int) -> list[str]:
    """
    Ambil codename dari kolom CODENAME_COL mulai ROW_START.
    Return list string (bisa kosong "") sesuai urutan baris.
    """
    range_end = ROW_START - 1 + n_rows
    resp = (
        service_sheet.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=f"{TAB_NAME}!{CODENAME_COL}{ROW_START}:{CODENAME_COL}{range_end}",
        )
        .execute()
    )
    rows = resp.get("values", [])
    # pad dengan "" agar panjang sama dengan n_rows
    result = [row[0].strip() if row else "" for row in rows]
    while len(result) < n_rows:
        result.append("")
    return result

def _normalize_codename(raw: str) -> str:
    """
    Ambil bagian yang relevan dari codename:
      'm1_arifqu' → 'arifqu'   (ada underscore → ambil setelah '_')
      'adhelia'   → 'adhelia'  (tidak ada underscore → pakai langsung)
    Hasil selalu casefold.
    """
    token = raw.split("_")[-1] if "_" in raw else raw
    return token.casefold()

def _match_codename_to_uid(codename: str, students: list[dict]) -> str | None:
    """
    Cek apakah token codename muncul sebagai substring
    di salah satu kata dalam fullname student (case-insensitive).
    Return user_id student yang cocok, atau None.
    """
    token = _normalize_codename(codename)
    if not token:
        return None
 
    for s in students:
        # pecah nama jadi kata-kata, cek substring per kata
        words = s["name"].casefold().split()
        if any(token in word for word in words):
            return s["user_id"]
 
    return None
  
def _apply_github_cell_formats(service_sheet, spreadsheet_id: str, sheet_id: int, rows: list[dict]):
    """
    Tulis username sebagai stringValue + textFormatRuns (underline, biru, hyperlink)
    ke kolom C. rows: list of { 'row_index': int (0-based), 'url': str }
    """
    requests = []
 
    for item in rows:
        row_idx = item["row_index"]   # 0-based
        url = item["url"]
        username = _extract_github_username(url)
        github_link = f"https://github.com/{username}"
 
        requests.append({
            "updateCells": {
                "rows": [{
                    "values": [{
                        "userEnteredValue": {"stringValue": username},
                        "textFormatRuns": [{
                            "startIndex": 0,
                            "format": {
                                "link": {"uri": github_link},
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
                "fields": "userEnteredValue,textFormatRuns",
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_idx,
                    "endRowIndex": row_idx + 1,
                    "startColumnIndex": 2,   # kolom C
                    "endColumnIndex": 3
                }
            }
        })
 
    if not requests:
        return
 
    service_sheet.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()


def _extract_github_link(submission: dict) -> str | None:
    assignment_sub = submission.get("assignmentSubmission", {})
    attachments = assignment_sub.get("attachments", [])
 
    for att in attachments:
        if "link" in att:
            url = att["link"].get("url", "")
            if "github.com" in url:
                return url
 
        if "driveFile" in att:
            url = att["driveFile"].get("alternateLink", "")
            if "github.com" in url:
                return url
 
    return None


# =============================================================================
# FUNGSI 1: Setup Nama Student ke Spreadsheet
# =============================================================================

def setup_nama(course_id: str, spreadsheet_id: str):
    print("\nMengambil data student dari Classroom...")
    students = _get_students(course_id)

    if not students:
        print("⚠️  Tidak ada student ditemukan.")
        return

    print(f"\nDitemukan {len(students)} student:")
    print(f"  {'No':<4} {'Nama'}")
    print(f"  {'-' * 4} {'-' * 30}")
    for i, s in enumerate(students, start=1):
        print(f"  {i:<4} {s['name']}")

    confirm = input(
        f"\nTulis Nama ke Spreadsheet (kolom {NAME_COL} tab '{TAB_NAME}')? (y/n) >> "
    ).strip().lower()
    if confirm != "y":
        print("⏭️  Dibatalkan.")
        return

    values = [[s["name"]] for s in students]

    service_sheet = get_service_sheets()
    range_end = ROW_START - 1 + len(values)
    range_target = f"{TAB_NAME}!{NAME_COL}{ROW_START}:{NAME_COL}{range_end}"

    service_sheet.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_target,
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()

    print(f"✅ {len(students)} nama berhasil ditulis ke '{TAB_NAME}'!{NAME_COL}{ROW_START}:{NAME_COL}{range_end}.")


# =============================================================================
# FUNGSI 2: Setup GitHub Profile ke Spreadsheet
# =============================================================================

def setup_github_profile(course_id: str, spreadsheet_id: str):
    work = _pick_coursework(course_id)
    if not work:
        return
 
    print(f"\nMengambil submisi untuk: {work['title']}...")
 
    service = get_service_courses()
    submissions_resp = (
        service.courses()
        .courseWork()
        .studentSubmissions()
        .list(courseId=course_id, courseWorkId=work["id"])
        .execute()
    )
    submissions = submissions_resp.get("studentSubmissions", [])
 
    # Build map: user_id → github_link
    github_map: dict[str, str] = {}
    for sub in submissions:
        link = _extract_github_link(sub)
        if link:
            github_map[sub["userId"]] = link
 
    print(f"  Link GitHub ditemukan: {len(github_map)} dari {len(submissions)} submisi.")
 
    students = _get_students(course_id)
 
    # Ambil nama & codename dari sheet (urutan baris sebagai acuan)
    service_sheet = get_service_sheets()
    range_end = ROW_START - 1 + len(students)
 
    sheet_resp = (
        service_sheet.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=f"{TAB_NAME}!{NAME_COL}{ROW_START}:{NAME_COL}{range_end}",
        )
        .execute()
    )
    sheet_names = [row[0] if row else "" for row in sheet_resp.get("values", [])]
 
    # Ambil codename dari kolom T, pad sesuai panjang sheet_names
    codenames = _fetch_codenames(service_sheet, spreadsheet_id, len(sheet_names))
 
    # Ambil nilai kolom C yang sudah ada — untuk skip baris yang sudah terisi
    existing_resp = (
        service_sheet.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=f"{TAB_NAME}!{REPO_COL}{ROW_START}:{REPO_COL}{range_end}",
        )
        .execute()
    )
    existing_col = [row[0].strip() if row else "" for row in existing_resp.get("values", [])]
    while len(existing_col) < len(sheet_names):
        existing_col.append("")
 
    table = []
    format_rows = []
 
    for i, sheet_name in enumerate(sheet_names):
        codename = codenames[i]
        uid = _match_codename_to_uid(codename, students) if codename else None
        link = github_map.get(uid, "") if uid else ""
        username = _extract_github_username(link) if link else ""
 
        sheet_row = ROW_START + i       # nomor baris di sheet (1-based)
        row_index = ROW_START - 1 + i   # 0-based untuk Sheets API
        already_filled = bool(existing_col[i])
 
        table.append({
            "row": sheet_row,
            "row_index": row_index,
            "name": sheet_name,
            "codename": codename,
            "username": username,
            "link": link,
            "skip": already_filled,
        })
 
        if link and not already_filled:
            format_rows.append({
                "row_index": row_index,
                "url": link,
            })
 
    # Preview
    print(f"\n{'Row':<5} {'Nama':<26} {'Codename':<16} {'Username':<20} {'Status'}")
    print("-" * 95)
    for item in table:
        if item["skip"]:
            status = "⏭  skip (sudah ada)"
        elif item["link"]:
            uname = item["username"][:18] + ".." if len(item["username"]) > 18 else item["username"]
            status = f"✓  {uname}"
        else:
            status = "—  kosong"
        print(
            f"{item['row']:<5} {item['name'][:26]:<26} {item['codename'][:16]:<16} "
            f"{item['username'][:20]:<20} {status}"
        )
    print("-" * 95)
 
    filled  = len(format_rows)
    skipped = sum(1 for t in table if t["skip"])
    empty   = len(table) - filled - skipped
    print(f"Total: {filled} akan ditulis, {skipped} di-skip, {empty} kosong.\n")
 
    confirm = input(
        f"Tulis ke Spreadsheet (kolom {REPO_COL} tab '{TAB_NAME}')? (y/n) >> "
    ).strip().lower()
    if confirm != "y":
        print("⏭️  Dibatalkan.")
        return
 
    sheet_id = _get_sheet_id(service_sheet, spreadsheet_id, TAB_NAME)
 
    print("Menulis username & format hyperlink...")
    _apply_github_cell_formats(service_sheet, spreadsheet_id, sheet_id, format_rows)
 
    # Kosongkan sel yang tidak punya link (dan belum terisi sebelumnya)
    empty_requests = []
    for item in table:
        if not item["link"] and not item["skip"]:
            empty_requests.append({
                "updateCells": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": item["row_index"],
                        "endRowIndex": item["row_index"] + 1,
                        "startColumnIndex": 2,
                        "endColumnIndex": 3,
                    },
                    "rows": [{"values": [{"userEnteredValue": {"stringValue": ""}}]}],
                    "fields": "userEnteredValue",
                }
            })
 
    if empty_requests:
        service_sheet.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": empty_requests}
        ).execute()
 
    print(f"✅ {filled} GitHub profile berhasil ditulis ke '{TAB_NAME}'!{REPO_COL} (underline, biru).")
    
    