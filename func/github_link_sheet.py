# setelah Lihat Work -> Pilih Work[i]
# kode ini mengelola >> Ambil GitHub → Clone & Spreadsheet

from config.cred import get_service_courses, get_service_sheets

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


# masukkan link github ke spreadsheet, ambil link ke codename buat git clone
def export_github(course_id, coursework_id, spreadsheet_id, n_student, tugas_ke):

    service_classroom = get_service_courses()
    service_sheets = get_service_sheets()

    print("\nMengambil submission dari Google Classroom...")

    submissions = (
        service_classroom.courses()
        .courseWork()
        .studentSubmissions()
        .list(courseId=course_id, courseWorkId=coursework_id)
        .execute()
    )

    github_map = {}

    for sub in submissions.get("studentSubmissions", []):
        user_id = sub["userId"]

        student = (
            service_classroom.courses()
            .students()
            .get(courseId=course_id, userId=user_id)
            .execute()
        )

        name = student["profile"]["name"]["fullName"]

        attachments = sub.get("assignmentSubmission", {}).get("attachments", [])

        repo = ""

        for att in attachments:
            if "link" in att:
                url = att["link"]["url"]

                if "github.com" in url:
                    parts = (
                        url.replace("https://github.com/", "")
                        .replace(".git", "")
                        .split("/")
                    )

                    repo = parts[0] + "/" + parts[1] if len(parts) > 1 else parts[0]
                    break

        print(f"Memproses {name} - {repo}")

        github_map[name.casefold()] = repo

    # =============================
    # Ambil nama dari spreadsheet
    # =============================
    tab_name = _get_tab_name(service_sheets, spreadsheet_id, tugas_ke)

    range_name = f"{tab_name}!B2:B{n_student + 1}"
    print(f"Mengambil nama dari {range_name}")

    sheet_data = (
        service_sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )

    names = sheet_data.get("values", [])

    # =============================
    # Ambil codename dari spreadsheet
    # =============================

    range_name = f"{tab_name}!F2:F{n_student + 1}"
    print(f"Mengambil codename dari {range_name}")

    sheet_code = (
        service_sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )

    codenames = sheet_code.get("values", [])

    # =============================
    # Pasangkan name + codename
    # =============================

    clone_commands = []

    for i, row in enumerate(names):
        name = row[0].strip()
        codename = ""

        if i < len(codenames):
            codename = codenames[i][0].strip()

        key = name.casefold()

        repo = github_map.get(key, "")

        if repo:
            url = f"https://github.com/{repo}.git"
            cmd = f"git clone {url} {codename}"
            clone_commands.append(cmd)
            print(f"{name} -> {cmd}")
        else:
            print(f"Repo tidak ditemukan untuk {name}")

    # =============================
    # Simpan ke clone.txt
    # =============================

    with open("clone.txt", "w", encoding="utf-8") as f:
        for cmd in clone_commands:
            f.write(cmd + "\n")

    print("clone.txt berhasil dibuat")

    spreadsheet_meta = (
        service_sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    )

    sheet_id = None

    for s in spreadsheet_meta["sheets"]:
        if s["properties"]["title"] == f"{tab_name}":
            sheet_id = s["properties"]["sheetId"]

    requests = []

    for i, row in enumerate(names):
        if not row:
            continue

        name = row[0]
        repo = github_map.get(name.casefold(), "")

        if not repo:
            continue

        url = f"https://github.com/{repo}"

        requests.append(
            {
                "updateCells": {
                    "start": {"sheetId": sheet_id, "rowIndex": i + 1, "columnIndex": 2},
                    "rows": [
                        {
                            "values": [
                                {
                                    "userEnteredValue": {"stringValue": repo},
                                    "textFormatRuns": [
                                        {
                                            "startIndex": 0,
                                            "format": {
                                                "link": {"uri": url},
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
                }
            }
        )

    if requests:
        service_sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

    print("Update spreadsheet selesai.")
