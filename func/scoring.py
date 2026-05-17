# ambil nilai dari data_score/{tugas_ke}{code}-score.txt
# masukkan score & notes ke sheet. masukkan #parameter sebagai note di {NOTE_COL}{ROW_START-1}
# (jika ada akses API) masukkan score ke course

import re
from config.cred import get_service_courses, get_service_sheets
import base64

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
    Ambil parameter, notes, minus
    """
    token_to_codename: dict[str, str] = {}
    for cn in codenames:
        token = cn.split("_")[-1] if "_" in cn else cn
        token_to_codename[token] = cn

    students = {cn: {"notes": [], "minus": 0} for cn in codenames}
    current_codename = None
    parameters: list[str] = []  # ← tambah
    in_parameter_block = False  # ← tambah

    with open(f"data_score/{tugas_ke}{code_class}-score.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # ← tambah: deteksi blok #parameter
            if line == "#parameter":
                in_parameter_block = True
                continue

            if in_parameter_block:
                if line == "":
                    in_parameter_block = False  # blok selesai di baris kosong
                    continue
                parameters.append(line)
                continue
            # ← sampai sini

            if line.startswith(">"):
                key = line[1:].strip().casefold()
                # coba exact match dulu, fallback ke token (bagian setelah "_" terakhir)
                key_token = (
                    key.split("_")[-1] if "_" in key else key
                )  # ← cth: codename m1_arifqu -> ariqzu
                matched = token_to_codename.get(key) or token_to_codename.get(
                    key_token
                )  # ← fix
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

    return students, parameters  # ← tambah return parameters


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
        note_short = (
            (item["notes"][:35] + "..") if len(item["notes"]) > 35 else item["notes"]
        )
        status = "📝 berubah (bold)" if item["changed"] else "  sama"
        print(
            template.format(
                item["row"], item["codename"][:20], note_short, item["score"], status
            )
        )

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
    students, parameters = _parse_score_txt(
        course_code, tugas_ke, codenames
    )  # ← unpack
    print(f"Score loaded: {len(students)} codename dari spreadsheet.")
    if parameters:
        print(f"Parameter ditemukan: {len(parameters)} baris.")

    # --- 3. Ambil score yang sudah ada di sheet ---
    existing_scores = _fetch_existing_scores(
        service_sheets, spreadsheet_id, tab_name, sheet_entries
    )

    # --- 4. Build updates & deteksi perubahan ---
    value_updates = []  # untuk values().batchUpdate (notes + score)
    bold_requests = []  # untuk spreadsheets().batchUpdate (format bold)
    table_data = []

    sheet_id = _get_sheet_id(service_sheets, spreadsheet_id, tab_name)
    score_col_i = _COL_INDEX[SCORE_COL]

    for sheet_row, codename in sheet_entries:
        if not codename or codename not in students:
            continue

        info = students[codename]
        score = info["score"]
        notes_display = ", ".join(info["notes"])
        notes_raw = "\n".join(info["notes"])
        prev_score = existing_scores.get(sheet_row)
        changed = prev_score != score  # None != score → juga dianggap berubah

        value_updates.append(
            {
                "range": f"{tab_name}!{NOTE_COL}{sheet_row}:{SCORE_COL}{sheet_row}",
                "values": [[notes_raw, score]],
            }
        )

        row_index = sheet_row - 1  # 0-based
        bold_requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_index,
                        "endRowIndex": row_index + 1,
                        "startColumnIndex": score_col_i,
                        "endColumnIndex": score_col_i + 1,
                    },
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": changed}}},
                    "fields": "userEnteredFormat.textFormat.bold",
                }
            }
        )

        table_data.append(
            {
                "row": sheet_row,
                "codename": codename,
                "notes": notes_display,
                "score": score,
                "prev_score": prev_score,
                "changed": changed,
            }
        )

    _print_table(table_data)

    # --- 5. Konfirmasi sebelum update Sheet ---
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit?gid={sheet_id}#gid={sheet_id}"
    print(f"🔗 {sheet_url}")
    confirm = input("Update ke Google Sheet? (y/n) >> ").strip().lower()
    if confirm == "y":
        # tulis notes & score
        service_sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": value_updates},
        ).execute()

        # tulis #parameter sebagai popup note di header notes
        if parameters:
            note_text = "\n".join(parameters)
            note_cell = f"{NOTE_COL}{ROW_START - 1}"
            service_sheets.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": [
                        {
                            "updateCells": {
                                "range": {
                                    "sheetId": sheet_id,
                                    "startRowIndex": ROW_START - 2,  # 0-based
                                    "endRowIndex": ROW_START - 1,
                                    "startColumnIndex": _COL_INDEX[NOTE_COL],
                                    "endColumnIndex": _COL_INDEX[NOTE_COL] + 1,
                                },
                                "rows": [{"values": [{"note": note_text}]}],
                                "fields": "note",
                            }
                        }
                    ]
                },
            ).execute()
            print(f"  📌 Parameter ditulis sebagai note di {note_cell}.")

        # terapkan bold pada score yang berubah
        if bold_requests:
            service_sheets.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": bold_requests},
            ).execute()
            changed_count = sum(1 for t in table_data if t["changed"])
            print(
                f"  {changed_count} nilai berubah → bold, {len(bold_requests) - changed_count} tidak berubah → unbold."
            )

        print("✅ Nilai berhasil dimasukkan ke Google Sheet.")
    else:
        print("⏭️  Update Sheet dilewati.")

    # --- 6. Update Classroom ---
    # Membuat link dinamis berdasarkan ID yang digunakan dalam script
    # --- Helper function untuk encoding ID ke Base64 (Google Style) ---
    def encode_id(raw_id):
        # Konversi ke string, lalu ke bytes, encode ke base64, dan bersihkan padding '='
        return base64.urlsafe_b64encode(str(raw_id).encode()).decode().strip("=")

    # Encode ID sebelum dimasukkan ke URL
    course_id_encoded = encode_id(course_id)
    coursework_id_encoded = encode_id(coursework_id)

    # Membuat link dinamis yang sesuai dengan format web Classroom
    classroom_url = (
        f"https://classroom.google.com/c/{course_id_encoded}/a/{coursework_id_encoded}"
        f"/submissions/by-status/and-sort-first-name/all"
    )

    print(f"\n🔗 Buka Classroom: {classroom_url}")
    confirm2 = input("\nUpdate ke Google Classroom? (y/n) >> ").strip().lower()
    if confirm2 != "y":
        print("⏭️  Update Classroom dilewati.")
        return

    # Pilihan mode update
    print("\nPilih mode update Classroom:")
    print("1. Hanya nilai yang berubah di Spreadsheet")
    print("2. Semua nilai (Total Update)")
    choice = input("Pilih (1/2) >> ").strip()

    if choice == "1":
        # Filter hanya codename yang berubah
        target_codenames = {t["codename"] for t in table_data if t["changed"]}
        mode_text = "hanya nilai yang berubah"
    else:
        # Ambil semua codename yang ada di table_data
        target_codenames = {t["codename"] for t in table_data}
        mode_text = "semua nilai"

    if not target_codenames:
        print("⏭️  Tidak ada data untuk di-update, skip Classroom.")
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
    print(f"\n🚀 Mengirim {len(target_codenames)} score ({mode_text}) ke Classroom...")

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

        matched_codename = None
        for codename in target_codenames:
            token = codename.split("_")[-1] if "_" in codename else codename
            if any(token in word for word in fullname.split()):
                matched_codename = codename
                break

        if not matched_codename:
            continue

        score = students[matched_codename]["score"]
        # Ambil nilai sebelumnya untuk log tampilan
        prev = next(
            (t["prev_score"] for t in table_data if t["codename"] == matched_codename),
            "N/A",
        )

        print(
            f"  Update {fullname} ({matched_codename}) → {score} (sebelumnya: {prev})"
        )

        service.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=coursework_id,
            id=submission_id,
            updateMask="assignedGrade,draftGrade",
            body={"assignedGrade": score, "draftGrade": score},
        ).execute()

    # --- Kembalikan Nilai (return) untuk semua submission ---
    print("\nMengembalikan nilai ke semua siswa...")
    returned_count = 0
    for sub in subs:
        try:
            service.courses().courseWork().studentSubmissions().return_(
                courseId=course_id,
                courseWorkId=coursework_id,
                id=sub["id"],
                body={},
            ).execute()
            returned_count += 1
        except Exception as e:
            print(f"  ⚠️  Gagal return submission {sub['id']}: {e}")

    print(f"✅ {returned_count}/{len(subs)} nilai dikembalikan ke siswa.")
