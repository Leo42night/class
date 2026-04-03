# ambil max score dari sheet (hitung dulu di sheet), push ke backend web ppwl
import sys
import os
import requests

sys.path.append(
    os.path.dirname(os.path.dirname(__file__))
)  # agar import env dapat diakses
from config.env import env
from config.cred import get_service_sheets

TAB = "Nilai"
START_ROW = 3
EMAIL_COL = "U"
COL_MAX_SCORE = "V"


def get_course_by_code(code):  # 'a' or 'b' -> cid, course_name

    cid = env.COURSE_ID_B if code.lower() == "b" else env.COURSE_ID_A
    return cid, f"Praktikum PWL 2026 {code.upper()}"


if __name__ == "__main__":
    print("Get Students Max Point: default kelas: a, opsi -> 'a' atau 'b'")
    print("Spreadsheet student score_max -> DB: user.score_max")
    code = sys.argv[1] if len(sys.argv) >= 2 else "a"

    course_id, course_name = get_course_by_code(code)
    cnf = env.get_config(code)
    SPREADSHEET_ID = cnf["spreadsheet"]
    N_STUDENT = cnf["n_student"]
    print(f"{course_name} | [{SPREADSHEET_ID}] | {N_STUDENT} students")

    service = get_service_sheets()
    sheet = service.spreadsheets()

    # Tentukan range: U3:V{START_ROW + N_STUDENT}
    range_name = (
        f"{TAB}!{EMAIL_COL}{START_ROW}:{COL_MAX_SCORE}{START_ROW + N_STUDENT - 1}"
    )

    print(f"Mengambil data dari range: {range_name}...")

    try:
        result = (
            sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        )

        rows = result.get("values", [])

        if not rows:
            print("Tidak ada data ditemukan.")
        else:
            print(f"Memproses {len(rows)} baris data ke {env.API_URL}/users/score...")

            for row in rows:
                # Lewati jika baris kosong atau email tidak ada
                if len(row) < 2:
                    continue

                email = row[0]  # Dari Kolom U
                score_max = row[1]  # Dari Kolom V

                # Payload untuk API Anda
                payload = {"email": email, "score_max": int(score_max)}

                # Kirim ke API (Asumsi menggunakan endpoint update score)
                url = f"{env.API_URL}/users/score"  # Sesuaikan endpoint Anda
                headers = {"Authorization": ""}

                try:
                    response = requests.put(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        print(f" Berhasil: {email} -> {score_max}")
                    else:
                        print(
                            f" Gagal: {email} | Status: {response.status_code} | {response.text}"
                        )
                except Exception as e:
                    print(f" Error saat hit API untuk {email}: {str(e)}")

    except Exception as err:
        print(f"Terjadi kesalahan pada Google Sheets API: {err}")

    print("Selesai.")
