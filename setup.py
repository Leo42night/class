import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(__file__))
)  # agar import env dapat diakses

from config.env import env
from func.setup_sheet import setup_nama, setup_github_profile


def get_course_by_code(code: str):
    return env.COURSE_ID_B if code.lower() == "b" else env.COURSE_ID_A, f"PPWL 2026 {code.upper()}"


def menu_loop(course_id: str, course_name: str, course_code: str):
    cfg = env.get_config(course_code)

    while True:
        print("\n====================")
        print(f"CLASS: {course_name} [{course_code.upper()}]")
        print("====================")
        print("1. Setup Spreadsheet Nama")
        print("2. Setup Spreadsheet Link Github Profile")
        print("0. Keluar")

        choice = input("Pilih menu >> ").strip()

        if choice == "1":
            setup_nama(
                course_id=course_id,
                spreadsheet_id=cfg["spreadsheet"]
            )

        elif choice == "2":
            setup_github_profile(
                course_id=course_id,
                spreadsheet_id=cfg["spreadsheet"]
            )

        elif choice == "0":
            break

        else:
            print("Pilihan tidak valid.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ppwl-setup <kelas>")
        print("Default: python setup.py a")
        code = 'a'
    else:
        code = sys.argv[1]

    course_id, course_name = get_course_by_code(code)

    menu_loop(course_id, course_name, code)