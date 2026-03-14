# ambil username github di spreadsheet, lalu berikan link github.com/<username> yang sesuai value username
# jadikan link tersebut sebagai request
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(__file__))
)  # agar import env dapat diakses
from config.env import env
from config.cred import service

# DATA
SPREADSHEET_ID = env.SPREADSHEET_ID_A
N_STUDENT = env.N_STUDENT_A

# Range username GitHub
ROW_AWAL = 3
RANGE = f"Nilai!C{ROW_AWAL}:C{N_STUDENT + ROW_AWAL - 1}"

# Ambil data dari spreadsheet
result = (
    service.spreadsheets()
    .values()
    .get(spreadsheetId=SPREADSHEET_ID, range=RANGE)
    .execute()
)

values = result.get("values", [])

if not values:
    print("Tidak ada data ditemukan.")
else:
    for row in values:
        username = row[0].strip()
        github_link = f"https://github.com/{username}"
        print(github_link)
