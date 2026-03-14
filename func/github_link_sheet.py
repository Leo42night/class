# setelah Lihat Work -> Pilih Work[i]
# kode ini mengelola >> Ambil GitHub → Clone & Spreadsheet

from config.cred import get_service_courses, get_service_sheets

ROW_START = 2
NAME_COL = "B"
REPO_COL = "C"
CODENAME_COL = "F"

_COL_INDEX = {col: i for i, col in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}


def _get_tab_name(service_sheets, spreadsheet_id, tugas_ke):
    meta = (
        service_sheets.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
        .execute()
    )
    prefix = f"{tugas_ke}#"
    print(f"\nSpreadsheet: periksa tab dengan prefix '{prefix}'...")
    for sheet in meta.get("sheets", []):
        title = sheet["properties"]["title"]
        if title.startswith(prefix):
            print(f"Tab ditemukan: '{title}'")
            return title
    raise ValueError(f"Tidak ada tab dengan prefix '{prefix}' di spreadsheet {spreadsheet_id}")


def _get_sheet_id(service_sheets, spreadsheet_id, tab_name):
    meta = service_sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for s in meta["sheets"]:
        if s["properties"]["title"] == tab_name:
            return s["properties"]["sheetId"]
    raise ValueError(f"Tab '{tab_name}' tidak ditemukan.")


def _fetch_col(service_sheets, spreadsheet_id, tab_name, col, n_rows):
    """Ambil satu kolom mulai ROW_START, return list string (di-pad '')."""
    range_str = f"{tab_name}!{col}{ROW_START}:{col}{ROW_START - 1 + n_rows}"
    resp = (
        service_sheets.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_str)
        .execute()
    )
    rows = resp.get("values", [])
    return [rows[i][0].strip() if i < len(rows) and rows[i] else "" for i in range(n_rows)]


def _clean_name(name: str) -> str:
    """Strip prefix 'panitia_' yang kadang muncul di nama Classroom."""
    clean = name.strip()
    if clean.lower().startswith("panitia_"):
        clean = clean[len("panitia_"):]
    return clean


def export_github(course_id, coursework_id, spreadsheet_id, n_student, course_code, tugas_ke):

    service_classroom = get_service_courses()
    service_sheets = get_service_sheets()

    # =============================
    # 1. Ambil submission Classroom
    # =============================
    print("\nMengambil submission dari Google Classroom...")

    submissions = (
        service_classroom.courses()
        .courseWork()
        .studentSubmissions()
        .list(courseId=course_id, courseWorkId=coursework_id)
        .execute()
    )

    # list of { name, repo } urut sesuai yang dikembalikan API
    classroom_data: list[dict] = []

    for sub in submissions.get("studentSubmissions", []):
        user_id = sub["userId"]

        student = (
            service_classroom.courses()
            .students()
            .get(courseId=course_id, userId=user_id)
            .execute()
        )

        raw_name = student["profile"]["name"]["fullName"]
        name = _clean_name(raw_name)
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

        print(f"  {name} → {repo or '(tidak ada)'}")
        classroom_data.append({"name": name, "repo": repo})

    # urutkan alphabetically agar konsisten dengan sheet
    classroom_data.sort(key=lambda x: x["name"].casefold())
    # =============================
    # 2. Ambil tab & codename dari sheet
    # =============================
    tab_name = _get_tab_name(service_sheets, spreadsheet_id, tugas_ke)
    sheet_id = _get_sheet_id(service_sheets, spreadsheet_id, tab_name)

    n_rows = max(n_student, len(classroom_data))
    codenames = _fetch_col(service_sheets, spreadsheet_id, tab_name, CODENAME_COL, n_rows)

    # build map: codename → index baris (0-based dari ROW_START)
    codename_to_idx: dict[str, int] = {
        cn.casefold(): i for i, cn in enumerate(codenames) if cn
    }

    # =============================
    # 3. Build requests & output
    # =============================
    requests    = []
    clone_commands = []
    zero_score  = []

    name_col_i = _COL_INDEX[NAME_COL]
    repo_col_i = _COL_INDEX[REPO_COL]
    
    special_case = {
        "christian": "dr C"
    }
    
    print(f"codename_to_idx: {codename_to_idx}")
    print(f"codenames raw: {codenames}")

    for entry in classroom_data:
        name = entry["name"]
        repo = entry["repo"]

        # cari baris berdasarkan kecocokan substring nama ke codename
        matched_idx = None
        name_lower  = name.casefold()
        for cn, idx in codename_to_idx.items():
            # token = bagian setelah '_' pertama jika ada
            token = cn.split("_")[-1] if "_" in cn else cn
            print(f"  {cn} - {name} → {token}")
            if token in name_lower:
                matched_idx = idx
                break
            if token in special_case and special_case[token].lower() in name_lower:
                matched_idx = idx
                break


        if matched_idx is None:
            print(f"  ⚠️  Tidak ada codename untuk '{name}', Skip (tambah di {tab_name}!{NAME_COL}...).")
            continue

        row_index = ROW_START - 1 + matched_idx   # 0-based untuk API
        # print(f"LOOP:  {name} → {repo or '(tidak ada)'}")
        # tulis name ke NAME_COL
        requests.append({
            "updateCells": {
                "start": {"sheetId": sheet_id, "rowIndex": row_index, "columnIndex": name_col_i},
                "rows": [{"values": [{"userEnteredValue": {"stringValue": name}}]}],
                "fields": "userEnteredValue",
            }
        })

        if repo:
            url = f"https://github.com/{repo}"
            codename = codenames[matched_idx]

            clone_commands.append(f"git clone {url}.git {codename}")

            # tulis repo link ke REPO_COL
            requests.append({
                "updateCells": {
                    "start": {"sheetId": sheet_id, "rowIndex": row_index, "columnIndex": repo_col_i},
                    "rows": [{
                        "values": [{
                            "userEnteredValue": {"stringValue": repo},
                            "textFormatRuns": [{
                                "startIndex": 0,
                                "format": {
                                    "link": {"uri": url},
                                    "underline": True,
                                    "foregroundColor": {"red": 0, "green": 0, "blue": 1},
                                },
                            }],
                        }]
                    }],
                    "fields": "userEnteredValue,textFormatRuns",
                }
            })
        else:
            codename = codenames[matched_idx]
            zero_score.append(f"> {codename}\n-100 Tidak mengumpulkan tugas")

    # =============================
    # 4. Batch update ke sheet
    # =============================
    if requests:
        service_sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()
        print(f"\nUpdate {len(classroom_data)} nama & repo ke spreadsheet selesai.")

    # =============================
    # 5. Simpan clone.txt
    # =============================
    with open("clone.txt", "w", encoding="utf-8") as f:
        for cmd in clone_commands:
            f.write(cmd + "\n")
    print(f"clone.txt berhasil dibuat ({len(clone_commands)} repo).")

    # =============================
    # 6. Simpan zero_score ke *-score.txt
    # =============================
    import os
    score_path = f"data_score/{course_code}-{tugas_ke}-score.txt"
 
    if os.path.exists(score_path):
        with open(score_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
 
        to_write = [e for e in zero_score if e.split("\n")[0] not in existing_content]
 
        with open(score_path, "a", encoding="utf-8") as f:
            f.write("\n") # pastikan tidak 1 line
            for entry in to_write:
                f.write(entry + "\n")
 
        skipped = len(zero_score) - len(to_write)
        print(f"{score_path} diperbarui (append): {len(to_write)} ditambah, {skipped} di-skip (sudah ada).")
    else:
        with open(score_path, "w", encoding="utf-8") as f:
            for entry in zero_score:
                f.write(entry + "\n")
        print(f"{score_path} dibuat ({len(zero_score)} tidak mengumpulkan).")