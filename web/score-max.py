# Rutin: ambil max score dari sheet (hitung dulu di sheet), push ke backend web ppwl
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
COL_MAX_SCORE = "Y"  # Diubah dari V ke Y


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
            sys.exit()

        # Filter data valid terlebih dahulu
        valid_data = []
        for row in rows:
            if len(row) >= 5 and row[0] and row[4] != "":
                valid_data.append({"email": row[0], "score": row[4]})

        if not valid_data:
            print("Tidak ada data valid (email/score kosong).")
            sys.exit()

        # --- TAMPILKAN DATA TERLEBIH DAHULU ---
        print("\n" + "=" * 40)
        print(f"{'EMAIL':<30} | {'MAX SCORE':<10}")
        print("-" * 40)
        for item in valid_data:
            print(f"{item['email']:<30} | {item['score']:<10}")
        print("=" * 40)
        print(f"Total: {len(valid_data)} data siap dipost.")

        # --- KONFIRMASI ---
        confirm = input(f"\nKirim data ke {env.API_URL}/users/score? (y/n): ")
        if confirm.lower() != "y":
            print("Proses dibatalkan.")
            sys.exit()

        # --- PROSES PUSH KE API ---
        print("\nMemproses push data...")
        for item in valid_data:
            email = item["email"]
            score_max = item["score"]

            payload = {"email": email, "score_max": int(score_max)}
            url = f"{env.API_URL}/users/score"
            headers = {"Authorization": ""}  # Isi token jika diperlukan

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
        print(f"Terjadi kesalahan: {err}")

    print("\nSelesai.")
