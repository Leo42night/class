import sys
from config.cred import get_service_courses
from func.github_link_sheet import export_github
from func.scoring import run_scoring
from func.post_coursework import run_data_tugas
from config.env import env


def get_coursework(course_id):
    service = get_service_courses()
    results = service.courses().courseWork().list(courseId=course_id).execute()
    return results.get("courseWork", [])


def get_course_by_code(code):  # 'a' or 'b' -> cid, course_name
    cid = env.COURSE_ID_B if code.lower() == "b" else env.COURSE_ID_A
    return cid, f"Praktikum PWL 2026 {code.upper()}"


def work_menu(course_id, course_code, work):
    cfg = env.get_config(course_code)

    while True:
        tugas_ke = int(work["title"].split("#")[0])
        print(f"\nWork: {work['title']} (Tugas ke: {tugas_ke})")
        print("1. Ambil GitHub → Clone & Spreadsheet")
        print("2. Input Scoring → Sheet & Classroom")
        print("0. Kembali")

        action = input(">> ").strip()

        if action == "1":
            export_github(
                course_id, work["id"], cfg["spreadsheet"], cfg["n_student"], tugas_ke
            )

        elif action == "2":
            run_scoring(
                course_id=course_id,
                coursework_id=work["id"],
                spreadsheet_id=cfg["spreadsheet"],
                name_class=cfg["name_class"],
                tugas_ke=tugas_ke,
            )

        elif action == "0":
            return

        else:
            print("Pilihan tidak valid.")


def menu_loop(course_id, course_name, course_code):
    while True:
        print("\n====================")
        print(f"CLASS: {course_name} [{course_code.upper()}]")
        print("====================")
        print("1. Lihat Work")
        print("2. Post Tugas Baru")
        print("0. Keluar")

        choice = input("Pilih menu >> ").strip()

        if choice == "1":
            coursework = get_coursework(course_id)

            if not coursework:
                print("Tidak ada assignment")
                continue

            print("\n=== Pilih Work ===")
            for i, w in enumerate(coursework, start=1):
                can_edit = w.get("associatedWithDeveloper", False)
                status = "✅ YES Can Edit" if can_edit else "❌ NO (UI Created)"
                print(f"{i}. {w['title']} | {status}")
            print("0. Kembali")

            choice_work = input("Pilih assignment >> ").strip()

            if choice_work == "0":
                continue

            try:
                idx = int(choice_work) - 1
                work = coursework[idx]
                work_menu(course_id, course_code, work)

            except Exception as e:
                print(f"An exception occurred: {e}")

        elif choice == "2":
            run_data_tugas(course_id)

        elif choice == "0":
            break

        else:
            print("Pilihan tidak valid")


if __name__ == "__main__":
    print("\n🌟 Program PPWL 2026 API (Classroom, Spreadsheet)! 🌟\n")
    print("pakai `ppwl b` untuk kelas B\n")
    code = sys.argv[1] if len(sys.argv) >= 2 else "a"

    course_id, course_name = get_course_by_code(code)
    menu_loop(course_id, course_name, code)
