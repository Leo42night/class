import re
from config.cred import get_service_courses, get_service_sheets

ROW_START = 2
NAME_COL = "B"
REPO_COL = "C"
CODENAME_COL = "F"
NOTE_COL = "D"
SCORE_COL = "E"


def _parse_score_txt(code_class, tugas_ke, codenames: list[str]):
    """
    Parse file *-score.txt dan pasangkan ke codenames dari spreadsheet.
 
    Alur match:
      - Baris "> adhelia" di score.txt → key 'adhelia'
      - Dicari apakah key tersebut adalah substring dari salah satu codename
        (misal codename 'm1_arifqu' → token 'arifqu' → match "> arifqu")
      - Jika cocok, notes & minus dicatat ke codename tersebut
 
    Parameters
    ----------
    codenames : list[str] — daftar codename (casefold) dari kolom F spreadsheet
    """
    # Build lookup: token → codename asli
    # token = bagian setelah '_' jika ada, else codename itu sendiri
    token_to_codename: dict[str, str] = {}
    for cn in codenames:
        token = cn.split("_")[-1] if "_" in cn else cn
        token_to_codename[token] = cn
 
    students = {cn: {"notes": [], "minus": 0} for cn in codenames}
    current_codename = None
 
    with open(f"data_score/{code_class}-{tugas_ke}-score.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
 
            if line.startswith(">"):
                key = line[1:].strip().casefold()
                # cari codename yang token-nya cocok dengan key di score.txt
                matched = token_to_codename.get(key)
                current_codename = matched if matched else None
                continue
 
            if line == "":
                current_codename = None
                continue
 
            if current_codename and line.startswith("-"):
                students[current_codename]["notes"].append(line)
                m = re.match(r"-([0-9]+)", line)
                if m:
                    students[current_codename]["minus"] += int(m.group(1))
 
    for cn in students:
        students[cn]["score"] = 100 - students[cn]["minus"]
 
    return students


def _get_tab_name(service_sheets, spreadsheet_id, tugas_ke):
    """
    Cari nama tab yang punya prefix '{tugas_ke}#' di spreadsheet.
    Return nama tab (str), atau raise ValueError jika tidak ditemukan.
    """
    meta = (
        service_sheets.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
        .execute()
    )

    prefix = f"{tugas_ke}#"
    for sheet in meta.get("sheets", []):
        title = sheet["properties"]["title"]
        if title.startswith(prefix):
            print(f"Tab ditemukan: '{title}'")
            return title

    raise ValueError(
        f"Tidak ada tab dengan prefix '{prefix}' di spreadsheet {spreadsheet_id}"
    )


def _fetch_sheet_codenames(service_sheets, spreadsheet_id, tab_name, n_rows):
    """
    Ambil kolom CODENAME_COL dari tab, mulai ROW_START.
    Return list of (row_number_1based, codename_str).
    Baris kosong tetap disertakan agar index baris akurat.
    """
    range_end = ROW_START - 1 + n_rows
    range_str = f"{tab_name}!{CODENAME_COL}{ROW_START}:{CODENAME_COL}{range_end}"

    result = (
        service_sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_str)
        .execute()
    )

    rows = result.get("values", [])
    entries = []
    for i in range(n_rows):
        sheet_row = ROW_START + i
        codename = rows[i][0].strip().casefold() if i < len(rows) and rows[i] else ""
        entries.append((sheet_row, codename))

    return entries


def _print_table(table_data):
    if not table_data:
        print("⚠️  Tidak ada data siswa yang cocok ditemukan.")
        return

    template = "{:<5} | {:<20} | {:<40} | {:<6}"
    header = template.format("Row", "Codename", "Notes Summary", "Score")
    sep = "-" * len(header)

    print(f"\n{sep}\n{header}\n{sep}")
    for item in table_data:
        note_short = (
            (item["notes"][:37] + "..") if len(item["notes"]) > 37 else item["notes"]
        )
        print(template.format(item["row"], item["codename"][:20], note_short, item["score"]))

    print(sep)
    print(f"Total: {len(table_data)} data siap di-update.\n")


def run_scoring(course_id, coursework_id, spreadsheet_id, course_code, tugas_ke):
    """
    Entry point yang dipanggil dari work_menu.

    Parameters
    ----------
    course_id       : str   — ID kelas di Classroom
    coursework_id   : str   — ID tugas di Classroom
    spreadsheet_id  : str   — ID Google Sheet kelas
    course_code     : str   — prefix file, misal 'a'
    tugas_ke        : int   — nomor tugas
    """

    # --- 1. Ambil tab & codename dari Sheet ---
    service_sheets = get_service_sheets()
    tab_name = _get_tab_name(service_sheets, spreadsheet_id, tugas_ke)
 
    # ambil dengan buffer baris agar tidak terpotong
    sheet_entries = _fetch_sheet_codenames(service_sheets, spreadsheet_id, tab_name, 50)
 
    # ekstrak list codename (non-empty) sebagai sumber kebenaran
    codenames = [cn for _, cn in sheet_entries if cn]
 
    # --- 2. Parse file txt, pasangkan ke codenames dari sheet ---
    students = _parse_score_txt(course_code, tugas_ke, codenames)
    print(f"Score loaded: {len(students)} codename dari spreadsheet.")
 
    updates = []
    table_data = []

    for sheet_row, codename in sheet_entries:
        if not codename:
            continue

        if codename not in students:
            continue

        info = students[codename]
        score = info["score"]
        notes_display = ", ".join(info["notes"])
        notes_raw = "\n".join(info["notes"])

        # tulis ke kolom NOTE_COL & SCORE_COL pada baris yang sama
        updates.append({
            "range": f"{tab_name}!{NOTE_COL}{sheet_row}:{SCORE_COL}{sheet_row}",
            "values": [[notes_raw, score]]
        })

        table_data.append({
            "row": sheet_row,
            "codename": codename,
            "notes": notes_display,
            "score": score
        })

    _print_table(table_data)

    # --- 3. Konfirmasi sebelum update Sheet ---
    confirm = input("Update ke Google Sheet? (y/n) >> ").strip().lower()
    if confirm == "y":
        service_sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": updates},
        ).execute()
        print("✅ Nilai berhasil dimasukkan ke Google Sheet.")
    else:
        print("⏭️  Update Sheet dilewati.")

    # --- 4. Update Classroom ---
    confirm2 = input("Update ke Google Classroom? (y/n) >> ").strip().lower()
    if confirm2 != "y":
        print("⏭️  Update Classroom dilewati.")
        return

    service = get_service_courses()
    submissions = (
        service.courses()
        .courseWork()
        .studentSubmissions()
        .list(courseId=course_id, courseWorkId=coursework_id)
        .execute()
    )

    subs = submissions.get("studentSubmissions", [])
    print(f"\nSubmit {len(subs)} score ke Classroom...")

    for sub in subs:
        user_id = sub["userId"]
        submission_id = sub["id"]

        student = (
            service.courses()
            .students()
            .get(courseId=course_id, userId=user_id)
            .execute()
        )

        fullname = student["profile"]["name"]["fullName"].casefold()

        # cari codename yang cocok dengan fullname student
        matched_codename = None
        for codename in students:
            if codename in fullname or any(codename in word for word in fullname.split()):
                matched_codename = codename
                break

        if not matched_codename:
            continue

        score = students[matched_codename]["score"]
        print(f"  Update {fullname} ({matched_codename}) → {score}")

        service.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=coursework_id,
            id=submission_id,
            updateMask="assignedGrade,draftGrade",
            body={"assignedGrade": score, "draftGrade": score},
        ).execute()

    print("✅ Nilai berhasil dimasukkan ke Classroom.")