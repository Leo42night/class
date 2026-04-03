import sys
import os

# Menyesuaikan path agar bisa import dari folder config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.env import env
from config.cred import get_service_courses


def get_course_info(code):
    cid = env.COURSE_ID_B if code.lower() == "b" else env.COURSE_ID_A
    name = f"Praktikum PWL 2026 {code.upper()}"
    return cid, name


def get_students(course_id):
    service = get_service_courses()
    results = service.courses().students().list(courseId=course_id).execute()
    return results.get("students", [])


def get_coursework(course_id):
    service = get_service_courses()
    results = service.courses().courseWork().list(courseId=course_id).execute()
    return results.get("courseWork", [])


def get_submissions(course_id, coursework_id):
    service = get_service_courses()
    results = (
        service.courses()
        .courseWork()
        .studentSubmissions()
        .list(courseId=course_id, courseWorkId=coursework_id)
        .execute()
    )
    return results.get("studentSubmissions", [])


def handle_students(course_id):
    students = get_students(course_id)
    if not students:
        print("Tidak ada siswa ditemukan.")
        return

    students.sort(key=lambda x: x["profile"]["name"]["fullName"])

    print(f"\n--- Daftar Siswa ({len(students)} orang) ---")
    for i, s in enumerate(students, 1):
        print(f"{i}. {s['profile']['name']['fullName']}")

    while True:
        choice = input(
            "\nPilih nomor siswa untuk detail (atau '0' untuk kembali): "
        ).strip()
        if choice == "0":
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(students):
                p = students[idx]["profile"]
                print("\n" + "=" * 40)
                print(f"Nama        : {p['name']['fullName']}")
                print(f"Gmail       : {p['emailAddress']}")
                print(f"Profile URL : {p.get('photoUrl', 'Tidak ada foto')}")
                print("=" * 40)
            else:
                print("Nomor di luar jangkauan.")
        except ValueError:
            print("Input tidak valid.")


def handle_coursework(course_id):
    coursework = get_coursework(course_id)
    if not coursework:
        print("Tidak ada assignment ditemukan.")
        return

    print("\n--- Daftar Assignment ---")
    for i, w in enumerate(coursework, start=1):
        can_edit = "✅" if w.get("associatedWithDeveloper") else "❌"
        print(f"{i}. {w['title']} | {can_edit} Dev Access")

    while True:
        choice = input(
            "\nPilih nomor tugas untuk lihat submisi (atau '0' untuk kembali): "
        ).strip()
        if choice == "0":
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(coursework):
                work = coursework[idx]
                print(f"\nMengambil submisi untuk: {work['title']}...")

                # Load student mapping untuk nama
                students = get_students(course_id)
                student_map = {
                    s["userId"]: s["profile"]["name"]["fullName"] for s in students
                }

                submissions = get_submissions(course_id, work["id"])

                print(
                    f"\n{'NO':<3} | {'NAMA SISWA':<30} | {'STATUS':<15} | {'NILAI':<5}"
                )
                print("-" * 60)
                for j, sub in enumerate(submissions, start=1):
                    name = student_map.get(sub["userId"], "Unknown Student")
                    status = sub.get("state", "UNKNOWN")
                    score = sub.get("assignedGrade", "-")
                    print(f"{j:<3} | {name[:30]:<30} | {status:<15} | {score:<5}")
            else:
                print("Nomor di luar jangkauan.")
        except ValueError:
            print("Input tidak valid.")


def main():
    code = sys.argv[1] if len(sys.argv) >= 2 else "a"
    course_id, course_name = get_course_info(code)

    while True:
        print(f"\n===== MAIN MENU: {course_name} =====")
        print("1. Lihat Daftar Student")
        print("2. Lihat Daftar Coursework (Submisi)")
        print("0. Keluar")

        main_choice = input("Pilih menu >> ").strip()

        if main_choice == "1":
            handle_students(course_id)
        elif main_choice == "2":
            handle_coursework(course_id)
        elif main_choice == "0":
            print("Bye!")
            break
        else:
            print("Pilihan tidak tersedia.")


if __name__ == "__main__":
    main()
