# Formulai value codename di tiap tab work ke main tab 'Nilai'
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.env import env
from config.cred import get_service_sheets

MAIN_TAB = "Nilai"
MAIN_COL_CODENAME = "T"
MAIN_ROW_CODENAME_START = 3
WORK_COL_CODENAME = "F"
WORK_ROW_CODENAME_START = 2


def get_course_by_code(code):
    cid = env.COURSE_ID_B if code == "b" else env.COURSE_ID_A
    return cid, f"Praktikum PWL 2026 [{code.upper()}]"


def _get_work_tabs(service, spreadsheet_id):
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

    # --- 1. Ambil semua tab work ---
    work_tabs = _get_work_tabs(service_sheet, SPREADSHEET_ID)
    print(f"Tab ditemukan: {list(work_tabs.keys())}")

    # --- 2. Ambil codename existing di main tab (untuk pengecekan) ---
    existing_range = (
        f"{MAIN_TAB}!{MAIN_COL_CODENAME}{MAIN_ROW_CODENAME_START}"
        f":{MAIN_COL_CODENAME}{MAIN_ROW_CODENAME_START + N_STUDENT - 1}"
    )
    existing = (
        service_sheet.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=existing_range)
        .execute()
        .get("values", [])
    )
    print(f"Codename existing di '{MAIN_TAB}': {len(existing)} baris terisi")

    # --- 2. Build formula per tab (work tab ← Nilai) ---
    data_updates = []
    for tugas_ke, tab_title in work_tabs.items():
        formulas = []
        for i in range(N_STUDENT):
            main_row = MAIN_ROW_CODENAME_START + i
            formulas.append([f"='{MAIN_TAB}'!{MAIN_COL_CODENAME}{main_row}"])

        target_range = (
            f"'{tab_title}'!{WORK_COL_CODENAME}{WORK_ROW_CODENAME_START}"
            f":{WORK_COL_CODENAME}{WORK_ROW_CODENAME_START + N_STUDENT - 1}"
        )
        data_updates.append({"range": target_range, "values": formulas})

    # --- 3. Preview ---
    print(f"\nPreview tab '{list(work_tabs.values())[0]}':")
    for row in data_updates[0]["values"][:3]:
        print(f"  {row[0]}")

    # --- 4. Konfirmasi & update ---
    confirm = (
        input(f"\nTulis formula codename ke {len(work_tabs)} tab work? (y/n) >> ")
        .strip()
        .lower()
    )
    if confirm != "y":
        print("⏭️  Dilewati.")
        sys.exit(0)

    service_sheet.spreadsheets().values().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": data_updates},
    ).execute()

    print(
        f"✅ Formula codename ditulis ke {len(work_tabs)} tab work, {N_STUDENT} baris per tab."
    )
