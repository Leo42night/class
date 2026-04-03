# simple: ambil data student (course) -> send ke ppwl POST api/users
import sys
from config.cred import get_service_courses
from config.env import env
import json
import requests


def get_course_by_code(code):  # 'a' or 'b' -> cid, course_name
    cid = env.COURSE_ID_B if code.lower() == "b" else env.COURSE_ID_A
    return cid, f"Praktikum PWL 2026 {code.upper()}"


def get_students(service, course_id):
    students = []

    results = service.courses().students().list(courseId=course_id).execute()

    for s in results.get("students", []):
        user_id = s["userId"]

        profile = service.userProfiles().get(userId=user_id).execute()

        students.append(
            {
                "email": profile.get("emailAddress"),
                "name": profile.get("name", {}).get("fullName"),
                "profile_url": profile.get("photoUrl"),
            }
        )

    return students


def send_to_api(students):
    url = "http://localhost:3000/api/users"

    for student in students:
        try:
            r = requests.post(url, json=student)

            if r.status_code == 200 or r.status_code == 201:
                print(f"✅ Success: {student['email']}")
            else:
                print(f"⚠️ Failed: {student['email']} -> {r.text}")

        except Exception as e:
            print(f"❌ Error {student['email']}:", e)


def save_students_to_json(students, filename="students.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(students, f, indent=4, ensure_ascii=False)

    print(f"✅ Data tersimpan ke {filename}")


if __name__ == "__main__":
    print("Get Students: default kelas: a, opsi -> 'a' atau 'b'")
    code = sys.argv[1] if len(sys.argv) >= 2 else "a"

    course_id, course_name = get_course_by_code(code)
    print(course_name)

    service = get_service_courses()

    students = get_students(service, course_id)

    print(f"📚 Total students: {len(students)}")
    print(students)

    save_students_to_json(students)
    # send_to_api(students)
