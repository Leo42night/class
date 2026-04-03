import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.env import env
from config.cred import get_service_sheets

TAB = "Nilai"
START_ROW_MAIN = 3
START_ROW_WORK = 2

COL_WORK_SCORE = "E"
COL_START = "D"  # Tugas ke-1
COL_END = "S"  # Tugas ke-16

COL_START_I = ord(COL_START) - ord("A")  # 3 (0-based)
COL_END_I = ord(COL_END) - ord("A")  # 18
N_TUGAS = COL_END_I - COL_START_I + 1  # 16


def get_course_by_code(code):
    cid = env.COURSE_ID_B if code == "b" else env.COURSE_ID_A
    return cid, f"Praktikum PWL 2026 [{code.upper()}]"


def _get_work_tabs(service, spreadsheet_id):
    """
    Return dict: tugas_ke (int) → tab_title (str), sorted 1..16.
    Hanya tab dengan prefix "{n}#".
    """
    meta = (
        service.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets.properties.title")
        .execute()
    )
    tabs = {}
    for sheet in meta.get("sheets", []):
        title = sheet["properties"]["title"]
        if "#" in title:
            prefix = title.split("#")[0]
            if prefix.isdigit():
                tabs[int(prefix)] = title
    return dict(sorted(tabs.items()))


def _fetch_scores_for_tab(service, spreadsheet_id, tab_title, n_student):
    """
    Ambil COL_WORK_SCORE dari tab work. Return list[str|None] panjang n_student.
    """
    range_str = (
        f"'{tab_title}'!{COL_WORK_SCORE}{START_ROW_WORK}"
        f":{COL_WORK_SCORE}{START_ROW_WORK + n_student - 1}"
    )
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_str)
        .execute()
    )
    rows = result.get("values", [])
    scores = []
    for i in range(n_student):
        scores.append(rows[i][0] if i < len(rows) and rows[i] else "")
    return scores


if __name__ == "__main__":
    print("Sheet add Tabscore: default kelas: a, opsi -> 'a' atau 'b'")
    code = sys.argv[1] if len(sys.argv) >= 2 else "a"
    small_code = code.lower()
    course_id, course_name = get_course_by_code(small_code)
    cnf = env.get_config(small_code)
    SPREADSHEET_ID = cnf["spreadsheet"]
    N_STUDENT = cnf["n_student"]
    print(f"{course_name} | [{SPREADSHEET_ID}] | {N_STUDENT} students")

    service_sheet = get_service_sheets()

    # --- 1. Ambil tab work yang tersedia ---
    work_tabs = _get_work_tabs(service_sheet, SPREADSHEET_ID)
    print(f"Tab ditemukan: {list(work_tabs.keys())}")

    # --- 2. Susun formula per tugas ---
    # formula_matrix[student_i][col_offset] = formula / None
    formula_matrix = [[""] * N_TUGAS for _ in range(N_STUDENT)]

    for tugas_ke, tab_title in work_tabs.items():
        col_i = COL_START_I + (tugas_ke - 1)
        if col_i > COL_END_I:
            print(f"  ⚠️  Tugas ke-{tugas_ke} melebihi kolom {COL_END}, dilewati.")
            continue

        for student_i in range(N_STUDENT):
            work_row = START_ROW_WORK + student_i
            formula_matrix[student_i][col_i - COL_START_I] = (
                f"='{tab_title}'!{COL_WORK_SCORE}{work_row}"
            )

        print(f"  ✅ {tab_title:30s} → kolom {chr(ord('A') + col_i)}")

    # --- 3. Preview ---
    print("Preview 3 baris pertama:")
    for i in range(min(3, N_STUDENT)):
        print(f"  Row {START_ROW_MAIN + i}: {formula_matrix[i]}")

    # --- 4. Konfirmasi ---
    confirm = input(f"\nUpdate ke '{TAB}'? (y/n) >> ").strip().lower()
    if confirm != "y":
        print("⏭️  Dilewati.")
        sys.exit(0)

    # --- 5. Hanya update kolom yang ada tabnya ---
    data_updates = []
    for tugas_ke, tab_title in work_tabs.items():
        col_i = COL_START_I + (tugas_ke - 1)
        if col_i > COL_END_I:
            continue

        col_letter = chr(ord("A") + col_i)
        col_formulas = [
            [formula_matrix[student_i][col_i - COL_START_I]]
            for student_i in range(N_STUDENT)
        ]
        data_updates.append(
            {
                "range": f"{TAB}!{col_letter}{START_ROW_MAIN}:{col_letter}{START_ROW_MAIN + N_STUDENT - 1}",
                "values": col_formulas,
            }
        )

    # --- Run Batch Update --
    service_sheet.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={
            "valueInputOption": "USER_ENTERED",  # agar formula di-parse
            "data": data_updates,  # per-kolom, skip yang tidak ada
        },
    ).execute()

    print(
        f"✅ {len(data_updates)} kolom berhasil ditulis ke '{TAB}' sebagai formula link."
    )
