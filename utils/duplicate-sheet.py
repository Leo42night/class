# menduplikasi sheet (dipakai untuk setup template pengumpulan tugas di spreadsheet)
# !!! Pakai ini ketika pertama buat sheet tugas. Buat 1 sheet utama dulu

import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(__file__))
)  # agar import env dapat diakses

from config.cred import service
from config.env import env

SPREADSHEET_ID = env.SPREADSHEET_ID_A
# siapkan tab utama dengan prefix akng
CURRENT_TAB = 6
SOURCE_sheets_NAME = f"{CURRENT_TAB}#"  # template sheet

sheet = service.spreadsheets()

# ambil metadata spreadsheet
spreadsheet = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()

source_sheets_id = None

for s in spreadsheet["sheets"]:
    if s["properties"]["title"] == SOURCE_sheets_NAME:
        source_sheets_id = s["properties"]["sheetId"]
        break

if source_sheets_id is None:
    raise Exception(f"Sheet '{SOURCE_sheets_NAME}' tidak ditemukan")


def duplicate_tab_sheets(new_sheets_name):

    existing_sheetss = [s["properties"]["title"] for s in spreadsheet["sheets"]]

    if new_sheets_name in existing_sheetss:
        print(f"{new_sheets_name} sudah ada, skip")
        return

    # hitung jumlah sheet untuk posisi paling kanan
    spreadsheet_meta = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_count = len(spreadsheet_meta["sheets"])

    request = {
        "requests": [
            {
                "duplicateSheet": {
                    "sourceSheetId": source_sheets_id,
                    "newSheetName": new_sheets_name,
                    "insertSheetIndex": sheet_count,  # append paling kanan
                }
            }
        ]
    }

    sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=request).execute()

    print(f"Berhasil membuat sheet: {new_sheets_name}")


# LOOP DUPLIKASI
for i in range(CURRENT_TAB + 1, CURRENT_TAB + (16 - CURRENT_TAB) + 1):
    new_sheets_name = f"{i}#"
    duplicate_tab_sheets(new_sheets_name)
