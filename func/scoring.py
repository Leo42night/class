import re
from config.cred import get_service_courses, get_service_sheets

ROW_START = 2
NAME_COL = "B"
REPO_COL = "C"
CODENAME_COL = "F"
NOTE_COL = "D"
SCORE_COL = "E"

_COL_INDEX = {col: i for i, col in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}


def _parse_score_txt(code_class, tugas_ke, codenames: list[str]):
    """
    Parse file *-score.txt dan pasangkan ke codenames dari spreadsheet.
    """
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


def _get_sheet_id(service_sheets, spreadsheet_id, tab_name):
    meta = service_sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for s in meta["sheets"]:
        if s["properties"]["title"] == tab_name:
            return s["properties"]["sheetId"]
    raise ValueError(f"Tab '{tab_name}' tidak ditemukan.")


def _fetch_sheet_codenames(service_sheets, spreadsheet_id, tab_name, n_rows):
    """
    Ambil kolom CODENAME_COL dari tab, mulai ROW_START.
    Return list of (row_number_1based, codename_str).
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


def _fetch_existing_scores(service_sheets, spreadsheet_id, tab_name, sheet_entries):
    """
    Ambil nilai kolom SCORE_COL untuk baris yang ada di sheet_entries.
    Return dict: sheet_row → nilai score (int/float) atau None jika kosong.
    """
    if not sheet_entries:
        return {}

    row_numbers = [r for r, cn in sheet_entries if cn]
    if not row_numbers:
        return {}

    range_str = (
        f"{tab_name}!{SCORE_COL}{min(row_numbers)}:{SCORE_COL}{max(row_numbers)}"
    )
    result = (
        service_sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_str)
        .execute()
    )

    values = result.get("values", [])
    existing: dict[int, int | None] = {}
    for sheet_row in row_numbers:
        # offset dari min row
        i = sheet_row - min(row_numbers)
        if i < len(values) and values[i]:
            try:
                existing[sheet_row] = int(values[i][0])
            except ValueError:
                existing[sheet_row] = None
        else:
            existing[sheet_row] = None

    return existing


def _print_table(table_data):
    if not table_data:
        print("⚠️  Tidak ada data siswa yang cocok ditemukan.")
        return

    template = "{:<5} | {:<20} | {:<38} | {:<6} | {}"
    header = template.format("Row", "Codename", "Notes Summary", "Score", "Status")
    sep = "-" * len(header)

    print(f"\n{sep}\n{header}\n{sep}")
    for item in table_data:
        note_short = (item["notes"][:35] + "..") if len(item["notes"]) > 35 else item["notes"]
        status = "📝 berubah (bold)" if item["changed"] else "  sama"
        print(template.format(item["row"], item["codename"][:20], note_short, item["score"], status))

    print(sep)
    changed = sum(1 for t in table_data if t["changed"])
    print(f"Total: {len(table_data)} data, {changed} nilai berubah.\n")


def run_scoring(course_id, coursework_id, spreadsheet_id, course_code, tugas_ke):
    """
    Entry point yang dipanggil dari work_menu.
    """

    # --- 1. Ambil tab & codename dari Sheet ---
    service_sheets = get_service_sheets()
    tab_name = _get_tab_name(service_sheets, spreadsheet_id, tugas_ke)

    sheet_entries = _fetch_sheet_codenames(service_sheets, spreadsheet_id, tab_name, 50)
    codenames = [cn for _, cn in sheet_entries if cn]

    # --- 2. Parse file txt ---
    students = _parse_score_txt(course_code, tugas_ke, codenames)
    print(f"Score loaded: {len(students)} codename dari spreadsheet.")

    # --- 3. Ambil score yang sudah ada di sheet ---
    existing_scores = _fetch_existing_scores(service_sheets, spreadsheet_id, tab_name, sheet_entries)

    # --- 4. Build updates & deteksi perubahan ---
    value_updates = []   # untuk values().batchUpdate (notes + score)
    bold_requests = []   # untuk spreadsheets().batchUpdate (format bold)
    table_data    = []

    sheet_id   = _get_sheet_id(service_sheets, spreadsheet_id, tab_name)
    score_col_i = _COL_INDEX[SCORE_COL]
    note_col_i  = _COL_INDEX[NOTE_COL]

    for sheet_row, codename in sheet_entries:
        if not codename or codename not in students:
            continue

        info          = students[codename]
        score         = info["score"]
        notes_display = ", ".join(info["notes"])
        notes_raw     = "\n".join(info["notes"])
        prev_score    = existing_scores.get(sheet_row)
        changed       = prev_score != score   # None != score → juga dianggap berubah

        value_updates.append({
            "range": f"{tab_name}!{NOTE_COL}{sheet_row}:{SCORE_COL}{sheet_row}",
            "values": [[notes_raw, score]]
        })

        row_index = sheet_row - 1   # 0-based
        bold_requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_index,
                    "endRowIndex": row_index + 1,
                    "startColumnIndex": score_col_i,
                    "endColumnIndex": score_col_i + 1,
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": changed}
                    }
                },
                "fields": "userEnteredFormat.textFormat.bold",
            }
        })

        table_data.append({
            "row": sheet_row,
            "codename": codename,
            "notes": notes_display,
            "score": score,
            "prev_score": prev_score,
            "changed": changed,
        })

    _print_table(table_data)

    # --- 5. Konfirmasi sebelum update Sheet ---
    confirm = input("Update ke Google Sheet? (y/n) >> ").strip().lower()
    if confirm == "y":
        # tulis notes & score
        service_sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": value_updates},
        ).execute()

        # terapkan bold pada score yang berubah
        if bold_requests:
            service_sheets.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": bold_requests},
            ).execute()
            changed_count = sum(1 for t in table_data if t["changed"])
            print(f"  {changed_count} nilai berubah → bold, {len(bold_requests) - changed_count} tidak berubah → unbold.")

        print("✅ Nilai berhasil dimasukkan ke Google Sheet.")
    else:
        print("⏭️  Update Sheet dilewati.")

    # --- 6. Update Classroom ---
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
        user_id      = sub["userId"]
        submission_id = sub["id"]

        student  = (
            service.courses()
            .students()
            .get(courseId=course_id, userId=user_id)
            .execute()
        )

        fullname = student["profile"]["name"]["fullName"].casefold()

        matched_codename = None
        for codename in students:
            token = codename.split("_")[-1] if "_" in codename else codename
            if any(token in word for word in fullname.split()):
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