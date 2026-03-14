import re
from config.cred import get_service_courses, get_service_sheets


def _parse_score_txt(code_class, tugas_ke):
    """Baca nama siswa dan file score txt, return dict students."""
    with open("clone.txt", encoding="utf-8") as f:
        codenames = []
        for line in f:
            line = line.strip()
            codenames.append(line.split()[-1])  # ambil codename di akhir line
    students = {n: {"notes": [], "minus": 0} for n in codenames}
    current_name = None

    with open(f"data_score/{code_class}-{tugas_ke}-score.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line.startswith(">"):
                name = line[1:].strip().casefold()
                current_name = name if name in students else None
                continue

            if line == "":
                current_name = None
                continue

            if current_name and line.startswith("-"):
                students[current_name]["notes"].append(line)
                m = re.match(r"-([0-9]+)", line)
                if m:
                    students[current_name]["minus"] += int(m.group(1))

    for name in students:
        students[name]["score"] = 100 - students[name]["minus"]

    return students


def _get_tab_name(service_sheets, spreadsheet_id, tugas_ke):
    """
    Cari nama tab yang punya prefix '{tugas_ke}#' di spreadsheet.
    Contoh: tab '5#ppwl' cocok untuk tugas_ke=5.
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


def _fetch_sheets_names(service_sheets, spreadsheet_id, range_sheets):
    """Ambil daftar nama dari sheet, return list of rows."""
    result = (
        service_sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_sheets)
        .execute()
    )
    print("\nSheet Key Loaded:", result)
    return result.get("values", [])


def _print_table(table_data):
    if not table_data:
        print("⚠️  Tidak ada data siswa yang cocok ditemukan.")
        return

    template = "{:<5} | {:<25} | {:<40} | {:<6}"
    header = template.format("Row", "Name", "Notes Summary", "Score")
    sep = "-" * len(header)

    print(f"\n{sep}\n{header}\n{sep}")
    for item in table_data:
        note_short = (
            (item["notes"][:37] + "..") if len(item["notes"]) > 37 else item["notes"]
        )
        print(
            template.format(item["row"], item["name"][:25], note_short, item["score"])
        )

    print(sep)
    print(f"Total: {len(table_data)} data siap di-update.\n")


def run_scoring(course_id, coursework_id, spreadsheet_id, name_class, tugas_ke):
    """
    Entry point yang dipanggil dari work_menu.

    Parameters
    ----------
    course_id       : str   — ID kelas di Classroom
    coursework_id   : str   — ID tugas di Classroom
    spreadsheet_id  : str   — ID Google Sheet kelas
    name_class      : str   — prefix file, misal 'a'
    tugas_ke        : int   — nomor tugas
    """

    # --- 1. Parse file txt ---
    students = _parse_score_txt(name_class, tugas_ke)

    # --- 2. Ambil Codename dari Sheet ---
    service_sheets = get_service_sheets()
    tab_name = _get_tab_name(service_sheets, spreadsheet_id, tugas_ke)
    range_sheets = f"{tab_name}!F2:F{2 + 40}"
    names_rows = _fetch_sheets_names(service_sheets, spreadsheet_id, range_sheets)

    updates = []
    table_data = []

    for i, row in enumerate(names_rows):
        if not row:
            continue
        # print("tampilkan row")
        # print("\n")
        # print(row[0])
        # print("\n")
        # print(row)
        # exit()
        name = row[0]
        key = name.casefold()

        if key not in students:
            continue

        info = students[key]
        score = info["score"]
        notes_display = ", ".join(info["notes"])
        notes_raw = "\n".join(info["notes"])

        updates.append(
            {"range": f"{tab_name}!D{i + 2}:E{i + 2}", "values": [[notes_raw, score]]}
        )

        table_data.append(
            {"row": i + 2, "name": name, "notes": notes_display, "score": score}
        )

    _print_table(table_data)

    # --- 3. Konfirmasi sebelum update ---
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

        name = student["profile"]["name"]["fullName"].casefold()

        if name not in students:
            continue

        score = students[name]["score"]
        print(f"  Update {name} → {score}")

        service.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=coursework_id,
            id=submission_id,
            updateMask="assignedGrade,draftGrade",
            body={"assignedGrade": score, "draftGrade": score},
        ).execute()

    print("✅ Nilai berhasil dimasukkan ke Classroom.")
