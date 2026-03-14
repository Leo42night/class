import sys
from auth import get_service
from func.github_link_sheet import export_github
from func.scoring import run_scoring

DATA_FILE = "init/courses.txt"

CLASS_CONFIG = {
    "A": {
        "spreadsheet": "REMOVED_SECRET",
        "n_student": 22,
        "name_class": "a",
    },
    "B": {
        "spreadsheet": "REMOVED_SECRET",
        "n_student": 36,
        "name_class": "b",
    },
}


def get_coursework(course_id):
    service = get_service()
    results = service.courses().courseWork().list(courseId=course_id).execute()
    return results.get("courseWork", [])
     


def get_course_by_code(code):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            lines = line.strip().split("|")
            if code == lines[0]:
                cid, name = lines[1], lines[2]
                return cid, name
    return None, None


def list_coursework(course_id, course_name):
    service = get_service()
    print(f"\n=== Coursework: {course_name} ===")
    results = service.courses().courseWork().list(courseId=course_id).execute()
    coursework = results.get("courseWork", [])

    if not coursework:
        print("No assignments found.")
        return

    print(f"\n{'Title':<30} | {'ID':<15} | {'Can Edit?':<10}")
    print("-" * 60)

    for item in coursework:
        title = item.get("title", "No Title")[:28]
        work_id = item.get("id")
        can_edit = item.get("associatedWithDeveloper", False)
        status = "✅ YES" if can_edit else "❌ NO (UI Created)"
        print(f"{title:<30} | {work_id:<15} | {status}")


def work_menu(course_id, course_code, work):
    cfg = CLASS_CONFIG[course_code]

    while True:
        tugas_ke = int(work['title'].split("#")[0])
        print(f"\nWork: {work['title']} (Tugas ke: {tugas_ke})")
        print("1. Ambil GitHub → Clone & Spreadsheet")
        print("2. Input Scoring → Sheet & Classroom")
        print("0. Kembali")

        action = input(">> ").strip()

        if action == "1":
            export_github(
                course_id,
                work["id"],
                cfg["spreadsheet"],
                cfg["n_student"],
                tugas_ke
            )

        elif action == "2":
            run_scoring(
                course_id=course_id,
                coursework_id=work["id"],
                spreadsheet_id=cfg["spreadsheet"],
                name_class=cfg["name_class"],
                tugas_ke=tugas_ke
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
        print("0. Keluar")

        choice = input("Pilih menu >> ").strip()

        if choice == "1":
            coursework = get_coursework(course_id)

            if not coursework:
                print("Tidak ada assignment")
                continue

            print("\n=== Pilih Work ===")
            for i, w in enumerate(coursework, start=1):
                can_edit = w.get('associatedWithDeveloper', False)
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

        elif choice == "0":
            break

        else:
            print("Pilihan tidak valid")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <kelas>")
        print("Contoh: python main.py A")
        sys.exit(1)

    code = sys.argv[1].upper()

    course_id, course_name = get_course_by_code(code.lower())

    if not course_id:
        print(f"Kelas [{code}] tidak ditemukan di {DATA_FILE}")
        sys.exit(1)

    menu_loop(course_id, course_name, code)