# buat template Tugas pakai script python (agar dapat dinilai juga lewat python)
# Fitur sudah diimplementasi di func/post_coursework.py

import datetime
from config.cred import get_service_courses


def create_formatted_assignment(course_id):
    service = get_service_courses()

    # 1. Title
    title = "6# Monorepo (phase 1 & 2)"

    # 2. Description (Bold and Lists)
    # Note: Use \n for new lines. Bold is usually achieved via **text** # but Classroom UI support varies; standard clear text is safest.
    description = (
        "Kerjakan proyek monorepo (phase 1 & 2), link ada di module tab 𝟲# 𝗠𝗼𝗻𝗼𝗿𝗲𝗽𝗼!\n\n"
        " ➤ kumpulkan:  𝗹𝗶𝗻𝗸 𝗿𝗲𝗽𝗼 𝗴𝗶𝘁𝗵𝘂𝗯 (pastikan dalam format ​̲𝗵​̲𝘁​̲𝘁​̲𝗽​̲𝘀​̲:​̲/​̲/​̲𝗴​̲𝗶​̲𝘁​̲𝗵​̲𝘂​̲𝗯​̲.​̲𝗰​̲𝗼​̲𝗺​̲/​̲<​̲𝘂​̲𝘀​̲𝗲​̲𝗿​̲𝗻​̲𝗮​̲𝗺​̲𝗲​̲>​̲/​̲𝗽​̲𝗽​̲𝘄​̲𝗹​̲𝟲​̲-​̲𝗺​̲𝗼​̲𝗻​̲𝗼​̲𝗿​̲𝗲​̲𝗽​̲𝗼)\n\n"
        "Jika berhasil harusnya tampilan seperti ini:."
    )

    # 3. Due Date & Time
    # Setting due date to 5 days from now
    due_date = datetime.date.today() + datetime.timedelta(days=5)
    # print(due_date)
    # exit()

    # 4. Assignment Body
    assignment_body = {
        "title": title,
        "description": description,
        "materials": [
            {
                "link": {
                    "url": "https://drive.google.com/file/d/1TDEnk29_nNXeQ83_KC6KMBV74SyLZdXh/view?usp=sharing",
                    "title": "contoh-phase-1-success.png",
                }
            },
            {
                "link": {
                    "url": "https://drive.google.com/file/d/1GvzxvnB9kwB42ksMhS5pxoMhtY-A-Dtz/view?usp=sharing",
                    "title": "contoh-phase-2-success.png",
                }
            },
        ],
        "state": "PUBLISHED",
        "maxPoints": 100,
        "workType": "ASSIGNMENT",
        "dueDate": {
            "year": due_date.year,
            "month": due_date.month,
            "day": due_date.day,
        },
        "dueTime": {
            "hours": 16,  # menyesuaikan UTC +7: 16:59 UTC +7 = 23:59 WIB
            "minutes": 59,
        },
    }

    try:
        coursework = (
            service.courses()
            .courseWork()
            .create(courseId=course_id, body=assignment_body)
            .execute()
        )

        print("✅ Assignment created successfully!")
        print(f"ID: {coursework.get('id')}")
        print(f"Link: {coursework.get('alternateLink')}")
        return coursework.get("id")

    except Exception as e:
        print(f"❌ Failed to create assignment: {e}")
        return None


# Usage

# COURSE_ID = "825125683344" # Praktikum PWL 2026 A
COURSE_ID = "825266594962"  # Praktikum PWL 2026 B
create_formatted_assignment(COURSE_ID)
