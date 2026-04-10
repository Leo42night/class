# 1. Panggil dari main.py -> Lihat Work -> Pilih Work[i]
# 2. >> Ambil Link Attached GitHub Repo in Course, Link lainnya, file, history
# 3. >> Setup Nama & Link Repo (spreadsheet), buat clone.txt berisi command clone
# Local Setup Work
# 4. mkdir C:/ppwl<n><code>-sub/ -> copy file in exp/ -> run clone.txt & bun install
# 5. Simpan zero_score ke *-score.txt -> buat shortcut ke file ini di C:/ppwl<n><code>-sub/

from config.cred import get_service_courses, get_service_sheets
import os
import subprocess
import shutil
import re
import hashlib

from googleapiclient.http import MediaIoBaseDownload
import io
import json

ROW_START = 2
NAME_COL = "B"
REPO_COL = "C"
CODENAME_COL = "F"

_COL_INDEX = {col: i for i, col in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
EXP_FOLDER = "exp"
REPO_FILE = "repo.txt"
CACHE_FILE = "data_cache/classroom_data_{coursework_id}.json"  # Single cache file
LINKS_FILE = "links.txt"  # in each repo


def _cache_path(coursework_id):
    os.makedirs("data_cache", exist_ok=True)
    return f"data_cache/classroom_data_{coursework_id}.json"


def _load_cache(coursework_id) -> dict | None:
    """Load single cache file containing all data"""
    path = _cache_path(coursework_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_cache(coursework_id, data: dict):
    """Save all data to single cache file"""
    path = _cache_path(coursework_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Cache disimpan: {path}")


def _get_tab_name(service_sheets, spreadsheet_id, tugas_ke):
    meta = (
        service_sheets.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties")
        .execute()
    )
    prefix = f"{tugas_ke}#"
    print(f"\nSpreadsheet: periksa tab dengan prefix '{prefix}'...")
    for sheet in meta.get("sheets", []):
        props = sheet["properties"]
        title = props["title"]
        if title.startswith(prefix):
            gid = props["sheetId"]
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit?gid={gid}#gid={gid}"
            print(f"Tab ditemukan: '{title}'")
            print(f"URL: {url}")
            return title, gid
    raise ValueError(
        f"Tidak ada tab dengan prefix '{prefix}' di spreadsheet {spreadsheet_id}"
    )


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
    return [
        rows[i][0].strip() if i < len(rows) and rows[i] else "" for i in range(n_rows)
    ]


def _get_coursework_deadline(service_classroom, course_id, coursework_id) -> str:
    """Ambil deadline coursework, return string 'YYYY-MM-DD' atau 'N/A'."""
    cw = (
        service_classroom.courses()
        .courseWork()
        .get(courseId=course_id, id=coursework_id)
        .execute()
    )
    due = cw.get("dueDate")
    if not due:
        return "N/A"
    return f"{due['year']}-{due['month']:02d}-{due['day']:02d}"


def _clean_name(name: str) -> str:
    """Strip prefix 'panitia_' yang kadang muncul di nama Classroom."""
    clean = name.strip()
    if clean.lower().startswith("panitia_"):
        clean = clean[len("panitia_") :]
    return clean


# ---- LOCAL EDIT ----
def create_symlink(folder_target, folder_link, name_file):
    if not os.path.exists(folder_link):
        os.makedirs(folder_link)
        print(f"Directory for symlink created: {folder_link}")

    BAT_PATH = "C:/Tools/symlink.bat"
    target = os.path.abspath(f"{folder_target}/{name_file}")
    link = os.path.abspath(f"{folder_link}/{name_file}")

    for attempt in range(1, 3):  # max 2x percobaan
        result = subprocess.run(
            [BAT_PATH, target, link],
            capture_output=True,
            text=True,
            shell=True,
        )

        if os.path.exists(link):
            if attempt > 1:
                print(
                    f"✅ {name_file} di {folder_target} → sekarang ada di {folder_link} (attempt {attempt})"
                )
            else:
                print(
                    f"✅ {name_file} di {folder_target} → sekarang ada di {folder_link}"
                )
            return True

        print(f"  ⚠️  Symlink belum terbuat (attempt {attempt}), coba lagi...")

    print(
        f"❌ Gagal buat symlink setelah 2x percobaan: {result.stderr.strip() or result.stdout.strip()}"
    )
    return False


def copy_files(target_dir):
    try:
        # 2. Buat folder tujuan jika belum ada
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Directory created: {target_dir}")

        # 3. Copy semua file dari exp/ ke folder tujuan
        if os.path.exists(EXP_FOLDER):
            shutil.copytree(EXP_FOLDER, target_dir, dirs_exist_ok=True)
            print(f"Files exp/ copied to {target_dir}")
        else:
            print(f"3. Warning: Source folder '{EXP_FOLDER}' not found.")

        # 3.2. Copy beberapa file ke target_dir
        if os.path.exists(REPO_FILE):
            shutil.copy2(REPO_FILE, target_dir)
            print(f"File {REPO_FILE} to {target_dir}")
        else:
            print(f"3.2. Warning: '{REPO_FILE}' not found.")
    except Exception as e:
        print(f"Critical Error: {e}")


# Setup List repo di local untuk dinilai
def selective_clone(target_dir, bat_path: str = "sparse_clone.bat"):
    # Simpan path awal agar bisa kembali jika terjadi error di subfolder
    root_path = os.getcwd()

    try:
        # Pastikan .bat ada sekali saja sebelum loop
        bat_abs = os.path.abspath(bat_path)
        if not os.path.exists(bat_abs):
            raise FileNotFoundError(f"File bat tidak ditemukan: {bat_abs}")

        # konfirmasi ingin melakukan clone (bisa dilakukan belakangan)
        confirm = input("\nLakukan cloning repo? (y/n) >> ").lower()
        if confirm != "y":
            print("⏭️  Clone repo Dilewati.")
            return

        # 4. Pindah ke direktori tujuan
        os.chdir(target_dir)

        if not os.path.exists(REPO_FILE):
            print(f"Error: {REPO_FILE} tidak ditemukan di {target_dir}")
            return

        with open(REPO_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip()]

        for line in lines:
            parts = line.split()
            if len(parts) < 2:
                continue

            repo_url, folder_name = parts[0], parts[1]

            if os.path.exists(folder_name):
                print(
                    f"\n[SKIP] Folder '{folder_name}' sudah ada. Melewati repo ini..."
                )
                continue

            print(f"\n--- Memulai Selective Clone: {folder_name} ---")

            try:
                # 5. Jalankan sparse_clone.bat dengan argumen repo_url dan folder_name
                #    .bat dijalankan dari target_dir, hasilnya folder baru di target_dir
                result = subprocess.run(
                    [bat_abs, repo_url, folder_name],
                    shell=True,
                    capture_output=True,
                    text=True,
                )

                print(result.stdout)

                if result.returncode != 0:
                    print(f"[ERROR] Clone gagal untuk '{folder_name}':")
                    print(result.stderr)
                    continue  # Jangan lanjut ke bun install jika clone gagal

                print(f"[OK] '{folder_name}' berhasil di-clone.")

            except subprocess.CalledProcessError as e:
                print(f"SKIP REPO: '{folder_name}' gagal: {e}")
                continue

    except Exception as e:
        print(f"Critical Error: {e}")
    finally:
        # Selalu pastikan balik ke folder awal
        os.chdir(root_path)


def _sanitize_filename(name):
    """Ganti karakter tidak valid di nama file dengan underscore."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = name.strip(". ")
    return name or "unnamed"


def _file_hash(path, chunk_size=8192):
    """Hitung MD5 hash dari file lokal."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _drive_file_hash(service_drive, file_id):
    """Ambil MD5 checksum file dari metadata Drive."""
    meta = service_drive.files().get(fileId=file_id, fields="md5Checksum").execute()
    return meta.get("md5Checksum")


# MIME type Google Docs → format export
_GDOCS_EXPORT = {
    "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
    ),
}


def download_history(
    service_classroom, course_id, coursework_id, codename_to_folder: dict[str, str]
):
    """
    Download submission history (state & grade) ke history.txt
    di masing-masing folder codename.
    """
    print("\n-- DOWNLOAD history submission --")

    submissions = (
        service_classroom.courses()
        .courseWork()
        .studentSubmissions()
        .list(courseId=course_id, courseWorkId=coursework_id)
        .execute()
        .get("studentSubmissions", [])
    )

    STATE_LABEL = {
        "NEW": "Belum dibuka",
        "CREATED": "Dibuat",
        "TURNED_IN": "Dikumpulkan",
        "RETURNED": "Dikembalikan",
        "RECLAIMED_BY_STUDENT": "Ditarik kembali oleh siswa",
    }

    for sub in submissions:
        user_id = sub["userId"]

        student = (
            service_classroom.courses()
            .students()
            .get(courseId=course_id, userId=user_id)
            .execute()
        )
        raw_name = _clean_name(student["profile"]["name"]["fullName"])
        name_lower = raw_name.casefold()

        # Match ke codename (sama seperti logika lainnya)
        special_case = {"christian": "dr C"}
        matched_codename = None
        matched_folder = None

        for codename, folder_path in codename_to_folder.items():
            token = codename.split("_")[-1] if "_" in codename else codename
            token_lower = token.casefold()
            if token_lower in name_lower:
                matched_codename = codename
                matched_folder = folder_path
                break
            if (
                token_lower in special_case
                and special_case[token_lower].lower() in name_lower
            ):
                matched_codename = codename
                matched_folder = folder_path
                break

        if not matched_folder:
            print(f"  ⚠️  Tidak ada folder untuk '{raw_name}', skip.")
            continue

        history = sub.get("submissionHistory", [])
        if not history:
            print(f"  [{matched_codename}] Tidak ada submission history.")
            continue

        lines = [
            f"Submission history — {raw_name}",
            f"{'=' * 48}",
        ]

        for h in history:
            if "stateHistory" in h:
                sh = h["stateHistory"]
                state_raw = sh.get("state", "?")
                state_str = STATE_LABEL.get(state_raw, state_raw)
                actor = sh.get("actorUserId", "")
                ts = sh.get("stateTimestamp", "")
                lines.append(f"[STATUS] {state_str}")
                if ts:
                    lines.append(f"         Waktu : {ts}")
                if actor:
                    lines.append(f"         Actor : {actor}")

            elif "gradeHistory" in h:
                gh = h["gradeHistory"]
                grade_type = gh.get("gradeChangeType", "?")
                points = gh.get("pointsEarned", "")
                max_points = gh.get("maxPoints", "")
                actor = gh.get("actorUserId", "")
                ts = gh.get("gradeTimestamp", "")
                grade_label = {
                    "DRAFT_GRADE_POINTS_EARNED_CHANGE": "Draft grade diubah",
                    "ASSIGNED_GRADE_POINTS_EARNED_CHANGE": "Grade ditetapkan",
                }.get(grade_type, grade_type)

                lines.append(f"[NILAI]  {grade_label}")
                if points != "":
                    lines.append(f"         Nilai : {points}/{max_points}")
                if ts:
                    lines.append(f"         Waktu : {ts}")
                if actor:
                    lines.append(f"         Actor : {actor}")

            lines.append("")  # spasi antar entri

        os.makedirs(matched_folder, exist_ok=True)
        history_path = os.path.join(matched_folder, "history.txt")

        # skip jika konten identik
        new_content = "\n".join(lines)
        if os.path.exists(history_path):
            with open(history_path, "r", encoding="utf-8") as f:
                if f.read() == new_content:
                    print(f"  ⏭️  [{matched_codename}] history.txt identik, skip.")
                    continue

        with open(history_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  ✅ [{matched_codename}] history.txt ({len(history)} entri)")


# Mapping mimeType gambar → ekstensi
_IMAGE_MIME_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/svg+xml": ".svg",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


def _download_drive_file(service_drive, file_id, file_name, dest_dir):
    """Download satu file dari Google Drive ke dest_dir."""
    try:
        file_name = _sanitize_filename(file_name)
        base, ext = os.path.splitext(file_name)

        meta = (
            service_drive.files()
            .get(fileId=file_id, fields="md5Checksum,mimeType")
            .execute()
        )
        drive_hash = meta.get("md5Checksum")
        mime_type = meta.get("mimeType", "")

        # cek apakah Google Drive Folder → simpan ke links.txt
        if mime_type == "application/vnd.google-apps.folder":
            folder_url = f"https://drive.google.com/drive/folders/{file_id}"
            ref_path = os.path.join(dest_dir, LINKS_FILE)
            existing_urls = set()
            if os.path.exists(ref_path):
                with open(ref_path, "r", encoding="utf-8") as f:
                    existing_urls = {line.strip() for line in f if line.strip()}
            if folder_url in existing_urls:
                print(f"  ⏭️  Drive folder link sudah ada (skip): {folder_url}")
                return True
            with open(ref_path, "a", encoding="utf-8") as f:
                f.write(f"{file_name}\n{folder_url}\n\n")
            print(f"  📁 Drive folder disimpan ke {LINKS_FILE}: {file_name}")
            return True

        export_info = _GDOCS_EXPORT.get(mime_type)
        if export_info:
            export_mime, export_ext = export_info
            base = base or file_name
            file_name = base + export_ext
            drive_hash = None
        elif not ext:
            inferred_ext = _IMAGE_MIME_EXT.get(mime_type)
            if inferred_ext:
                file_name = file_name + inferred_ext

        base, ext = os.path.splitext(file_name)

        candidate = file_name
        counter = 2
        while os.path.exists(os.path.join(dest_dir, candidate)):
            local_path = os.path.join(dest_dir, candidate)
            if drive_hash and _file_hash(local_path) == drive_hash:
                print(f"  ⏭️  Identik, skip: {candidate}")
                return True
            if not drive_hash and ext in (".pdf", ".docx", ".xlsx", ".pptx"):
                print(f"  ⏭️  Export sudah ada, skip: {candidate}")
                return True
            candidate = f"{base}_{counter}{ext}"
            counter += 1

        file_path = os.path.join(dest_dir, candidate)

        if export_info:
            request = service_drive.files().export_media(
                fileId=file_id, mimeType=export_mime
            )
        else:
            request = service_drive.files().get_media(fileId=file_id)

        with io.FileIO(file_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

        print(f"  ✅ Downloaded: {candidate}")
        return True

    except Exception as e:
        print(f"  ❌ Gagal download '{file_name}': {e}")

        url = f"https://drive.google.com/file/d/{file_id}/view"
        ref_path = os.path.join(dest_dir, "links.txt")

        existing_urls = set()
        if os.path.exists(ref_path):
            with open(ref_path, "r", encoding="utf-8") as f:
                existing_urls = {line.strip() for line in f if line.strip()}
        if url in existing_urls:
            print(f"  ⏭️  Link sudah ada (skip): {url}")
            return False
        with open(ref_path, "a", encoding="utf-8") as f:
            f.write(f"{file_name}\n{url}\n\n")
        print(f"  🔗 Disimpan ke links.txt: {file_name}")

        if "file_path" in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"  🗑️  File kosong dihapus: {os.path.basename(file_path)}")
            except Exception:
                pass
        return False


def download_submissions(
    service_classroom, course_id, coursework_id, codename_to_folder: dict[str, str]
):
    """Download semua attachment submission ke masing-masing folder codename."""
    from config.cred import get_service_drive

    service_drive = get_service_drive()

    print("\n-- DOWNLOAD SUBMISSIONS --")

    submissions = (
        service_classroom.courses()
        .courseWork()
        .studentSubmissions()
        .list(courseId=course_id, courseWorkId=coursework_id)
        .execute()
        .get("studentSubmissions", [])
    )

    for sub in submissions:
        user_id = sub["userId"]
        student = (
            service_classroom.courses()
            .students()
            .get(courseId=course_id, userId=user_id)
            .execute()
        )
        raw_name = _clean_name(student["profile"]["name"]["fullName"])
        name_lower = raw_name.casefold()

        special_case = {"christian": "dr C"}
        matched_codename = None
        matched_folder = None

        for codename, folder_path in codename_to_folder.items():
            token = codename.split("_")[-1] if "_" in codename else codename
            token_lower = token.casefold()
            if token_lower in name_lower:
                matched_codename = codename
                matched_folder = folder_path
                break
            if (
                token_lower in special_case
                and special_case[token_lower].lower() in name_lower
            ):
                matched_codename = codename
                matched_folder = folder_path
                break

        if not matched_folder:
            print(f"  ⚠️  Tidak ada folder untuk '{raw_name}', skip.")
            continue

        attachments = sub.get("assignmentSubmission", {}).get("attachments", [])

        if not attachments:
            print(f"\n  [{matched_codename}] Tidak ada attachment.")
            continue

        print(f"\n  [{matched_codename}] {raw_name} — {len(attachments)} attachment(s)")
        os.makedirs(matched_folder, exist_ok=True)

        seen_github = set()

        for att in attachments:
            if "driveFile" in att:
                drive = att["driveFile"]
                file_id = drive["id"]
                file_name = drive.get("title", file_id)
                _download_drive_file(service_drive, file_id, file_name, matched_folder)

            elif "link" in att:
                url = att["link"]["url"]
                title = att["link"].get("title", url)
                ref_path = os.path.join(matched_folder, LINKS_FILE)

                existing_urls = set()
                if os.path.exists(ref_path):
                    with open(ref_path, "r", encoding="utf-8") as f:
                        existing_urls = {line.strip() for line in f if line.strip()}

                if "github.com" in url:
                    if url in existing_urls or url in seen_github:
                        print(f"  ⏭️  GitHub link sudah ada (skip): {url}")
                    elif not seen_github:
                        seen_github.add(url)
                        print(f"  ⏭️  GitHub link (skip): {url}")
                    else:
                        with open(ref_path, "a", encoding="utf-8") as f:
                            f.write(url + "\n")
                        seen_github.add(url)
                        print(
                            f"  🔗 GitHub link ke-{len(seen_github)} disimpan ke {LINKS_FILE}: {url}"
                        )
                    continue

                if url in existing_urls:
                    print(f"  ⏭️  Link sudah ada (skip): {url}")
                    continue
                with open(ref_path, "a", encoding="utf-8") as f:
                    f.write(url + "\n")
                print(f"  🔗 Link disimpan ke {LINKS_FILE}: {url}")

            elif "youTubeVideo" in att:
                yt = att["youTubeVideo"]
                video_url = f"https://youtu.be/{yt['id']}"
                title = yt.get("title", yt["id"])
                ref_path = os.path.join(matched_folder, "youtube.txt")
                existing_urls = set()
                if os.path.exists(ref_path):
                    with open(ref_path, "r", encoding="utf-8") as f:
                        existing_urls = {line.strip() for line in f if line.strip()}
                if video_url in existing_urls:
                    print(f"  ⏭️  Link sudah ada (skip): {video_url}")
                    continue
                with open(ref_path, "a", encoding="utf-8") as f:
                    f.write(f"{title}\n{video_url}\n\n")
                print(f"  ▶️  YouTube disimpan ke youtube.txt: {title}")

            elif "form" in att:
                form = att["form"]
                form_url = form.get("formUrl", "")
                title = form.get("title", "form")
                ref_path = os.path.join(matched_folder, "forms.txt")
                existing_urls = set()
                if os.path.exists(ref_path):
                    with open(ref_path, "r", encoding="utf-8") as f:
                        existing_urls = {line.strip() for line in f if line.strip()}
                if form_url in existing_urls:
                    print(f"  ⏭️  Link sudah ada (skip): {form_url}")
                    continue
                with open(ref_path, "a", encoding="utf-8") as f:
                    f.write(f"{title}\n{form_url}\n\n")
                print(f"  📋 Form disimpan ke forms.txt: {title}")

            else:
                print(f"  ❓ Tipe attachment tidak dikenal: {list(att.keys())}")


# ---- Entry Function ----
def export_github(
    course_id, coursework_id, spreadsheet_id, n_student, course_code, tugas_ke
):

    service_classroom = get_service_courses()
    service_sheets = get_service_sheets()

    # =============================
    # 1. Load atau buat cache tunggal
    # =============================
    cache_data = _load_cache(coursework_id)

    if cache_data and cache_data.get("submissions"):
        print(f"\nCache ditemukan ({len(cache_data['submissions'])} submissions).")
        use_cache = input("Gunakan cache? (y/n) >> ").strip().lower()
        if use_cache == "y":
            instruction_link = cache_data["instruction_link"]
            classroom_data = cache_data["submissions"]
            repo_folder = cache_data.get("repo_list", [])
            zero_score = cache_data.get("zero_score_list", [])
            print(
                f"Loaded dari cache: {len(classroom_data)} submissions, {len(repo_folder)} repos, {len(zero_score)} zero_score"
            )
        else:
            instruction_link = None
            classroom_data, repo_folder, zero_score = None, None, None
    else:
        instruction_link = None
        classroom_data, repo_folder, zero_score = None, None, None
        use_cache = "n"

    if use_cache != "y" or not cache_data:
        print("\nMengambil submission dari Google Classroom...")

        submissions = (
            service_classroom.courses()
            .courseWork()
            .studentSubmissions()
            .list(courseId=course_id, courseWorkId=coursework_id)
            .execute()
        )

        classroom_data = []
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

        classroom_data.sort(key=lambda x: x["name"].casefold())

        # =============================
        # 2. Ambil tab & codename dari sheet
        # =============================
        tab_name, tab_gid = _get_tab_name(service_sheets, spreadsheet_id, tugas_ke)

        n_rows = max(n_student, len(classroom_data))
        codenames = _fetch_col(
            service_sheets, spreadsheet_id, tab_name, CODENAME_COL, n_rows
        )

        # =============================
        # 3. Build repo_folder dan zero_score dari classroom_data
        # =============================
        repo_folder = []
        zero_score = []
        special_case = {"christian": "dr C"}
        codename_to_idx: dict[str, int] = {
            cn.casefold(): i for i, cn in enumerate(codenames) if cn
        }

        for entry in classroom_data:
            name = entry["name"]
            repo = entry["repo"]

            matched_idx = None
            name_lower = name.casefold()
            for cn, idx in codename_to_idx.items():
                token = cn.split("_")[-1] if "_" in cn else cn
                if token in name_lower:
                    matched_idx = idx
                    break
                if token in special_case and special_case[token].lower() in name_lower:
                    matched_idx = idx
                    break

            if matched_idx is None:
                continue

            codename = codenames[matched_idx]
            if repo:
                repo_folder.append(f"https://github.com/{repo}.git {codename}")
            else:
                zero_score.append(f"> {codename}\n-100 Tidak mengumpulkan tugas")

        # =============================
        # 4. Update spreadsheet jika diperlukan
        # =============================
        confirm_sheet = (
            input(
                f"\nUpdate data sheet [Nama,Repo] by Codename ke '{tab_name}'? (y/n) >> "
            )
            .strip()
            .lower()
        )

        if confirm_sheet == "y":
            sheet_id = tab_gid
            name_col_i = _COL_INDEX[NAME_COL]
            repo_col_i = _COL_INDEX[REPO_COL]
            requests = []

            for entry in classroom_data:
                name = entry["name"]
                repo = entry["repo"]

                matched_idx = None
                name_lower = name.casefold()
                for cn, idx in codename_to_idx.items():
                    token = cn.split("_")[-1] if "_" in cn else cn
                    if token in name_lower:
                        matched_idx = idx
                        break
                    if (
                        token in special_case
                        and special_case[token].lower() in name_lower
                    ):
                        matched_idx = idx
                        break

                if matched_idx is None:
                    continue

                row_index = ROW_START - 1 + matched_idx
                requests.append(
                    {
                        "updateCells": {
                            "start": {
                                "sheetId": sheet_id,
                                "rowIndex": row_index,
                                "columnIndex": name_col_i,
                            },
                            "rows": [
                                {
                                    "values": [
                                        {"userEnteredValue": {"stringValue": name}}
                                    ]
                                }
                            ],
                            "fields": "userEnteredValue",
                        }
                    }
                )

                if repo:
                    url = f"https://github.com/{repo}"
                    requests.append(
                        {
                            "updateCells": {
                                "start": {
                                    "sheetId": sheet_id,
                                    "rowIndex": row_index,
                                    "columnIndex": repo_col_i,
                                },
                                "rows": [
                                    {
                                        "values": [
                                            {
                                                "userEnteredValue": {
                                                    "stringValue": repo
                                                },
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
                print(
                    f"\nUpdate {len(classroom_data)} nama & repo ke spreadsheet selesai."
                )

        # Di dalam fungsi utama setelah coursework_id ditentukan
        coursework_detail = (
            service_classroom.courses()
            .courseWork()
            .get(courseId=course_id, id=coursework_id)
            .execute()
        )

        # Ini adalah link ke instruksi/petunjuk tugas
        instruction_link = coursework_detail.get("alternateLink", "")

        # =============================
        # 5. Simpan ke cache tunggal
        # =============================
        cache_data = {
            "instruction_link": instruction_link,
            "submissions": classroom_data,
            "repo_list": repo_folder,
            "zero_score_list": zero_score,
            "coursework_id": coursework_id,
            "course_id": course_id,
        }
        _save_cache(coursework_id, cache_data)

    # =============================
    # 6. Simpan file repo.txt
    # =============================
    with open(REPO_FILE, "w", encoding="utf-8") as f:
        for line in repo_folder:
            f.write(line + "\n")
    print(f"{REPO_FILE} berhasil dibuat ({len(repo_folder)} repo).")

    # =============================
    # 7. Simpan zero_score ke {n}{x}-score.txt
    # =============================
    score_path = f"data_score/{tugas_ke}{course_code}-score.txt"
    deadline = _get_coursework_deadline(service_classroom, course_id, coursework_id)
    header = (
        f"#parameter\n- instruction_link: {instruction_link}\n- deadline: {deadline}\n"
    )

    if not os.path.exists(score_path):
        with open(score_path, "w", encoding="utf-8") as f:
            f.write(header)
        print(f"{score_path} dibuat dengan header parameter.")
    else:
        with open(score_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
        if "#parameter" not in existing_content:
            with open(score_path, "w", encoding="utf-8") as f:
                f.write(header + "\n" + existing_content)
            print(f"{score_path} diperbarui: header #parameter ditambahkan.")

    if os.path.exists(score_path):
        with open(score_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        to_write = [e for e in zero_score if e.split("\n")[0] not in existing_content]

        with open(score_path, "a", encoding="utf-8") as f:
            f.write("\n")
            for entry in to_write:
                f.write(entry + "\n")

        skipped = len(zero_score) - len(to_write)
        print(
            f"{score_path} diperbarui (append): {len(to_write)} ditambah, {skipped} di-skip (sudah ada)."
        )
    else:
        with open(score_path, "w", encoding="utf-8") as f:
            for entry in zero_score:
                f.write(entry + "\n")
        print(f"{score_path} dibuat ({len(zero_score)} tidak mengumpulkan).")

    # =============================
    # 8. Local setup
    # =============================
    create_symlink(
        "C:/Users/ADVAN/repou/class/data_score",
        f"C:/repo/ppwl{tugas_ke}{course_code}-sub",
        f"{tugas_ke}{course_code}-score.txt",
    )

    target_local = f"C:/repo/ppwl{tugas_ke}{course_code}-sub"
    copy_files(target_local)
    selective_clone(target_local)

    # Build map codename → absolute path folder
    tab_name, _ = _get_tab_name(service_sheets, spreadsheet_id, tugas_ke)
    n_rows = max(n_student, len(cache_data["submissions"]))
    codenames = _fetch_col(
        service_sheets, spreadsheet_id, tab_name, CODENAME_COL, n_rows
    )

    codename_to_folder = {
        codename: os.path.join(target_local, codename)
        for codename in codenames
        if codename
    }

    confirm_dl = input("\nDownload attachment submission? (y/n) >> ").strip().lower()
    if confirm_dl == "y":
        download_submissions(
            service_classroom, course_id, coursework_id, codename_to_folder
        )
    else:
        print("⏭️  Download attachment dilewati.")

    confirm_dh = input("\nDownload submission history? (y/n) >> ").strip().lower()
    if confirm_dh == "y":
        print("\nDownload submission history ke history.txt")
        download_history(
            service_classroom, course_id, coursework_id, codename_to_folder
        )
    else:
        print("⏭️  Download submission history dilewati.")

    print(f"\nInstruction Link: {instruction_link}")

    # =============================
    # Verifikasi Buka Folder & VS Code
    # =============================
    open_code = input("\nBuka folder di VS Code? (y/n) >> ").strip().lower()

    if open_code == "y":
        print(f"🚀 Membuka {target_local}...")

        # Menggunakan shell=True agar bisa menjalankan command internal seperti 'cd'
        # dan memanggil 'code' yang biasanya ada di PATH.
        # Perintah: berpindah drive (jika perlu), cd ke folder, lalu buka VS Code.

        cmd = f'cd /d "{target_local}" && code .'
        subprocess.Popen(cmd, shell=True)
    else:
        print("\nSelesai. Jika ingin masuk manual, jalankan:")
        print(f"cd /d {target_local} && code .")
