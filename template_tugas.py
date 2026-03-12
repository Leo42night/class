# buat template Tugas pakai script python (agar dapat dinilai juga lewat python)

import datetime
from auth import get_service
# Assuming get_service() is already defined in your script with proper SCOPES

def create_formatted_assignment(course_id):
    service = get_service()

    # 1. Title
    title = "Tugas 5: Project Structure (Automated)"

    # 2. Description (Bold and Lists)
    # Note: Use \n for new lines. Bold is usually achieved via **text** # but Classroom UI support varies; standard clear text is safest.
    description = (
        "**PENTING: Bacalah instruksi di bawah ini!**\n\n"
        "Silahkan kerjakan project dengan ketentuan:\n"
        "* Gunakan struktur folder Monorepo.\n"
        "* Pastikan Middleware sudah terpasang.\n"
        "* Link dokumentasi: https://example.com/guide\n\n"
        "Tugas ini akan ditutup otomatis setelah batas waktu."
    )

    # 3. Due Date & Time
    # Setting due date to 7 days from now
    due_date = datetime.date.today() + datetime.timedelta(days=7)
    
    # 4. Assignment Body
    assignment_body = {
        "title": title,
        "description": description,
        "materials": [
            {"link": {"url": "https://bun.sh/docs", "title": "Dokumentasi Bun.js"}}
        ],
        "state": "PUBLISHED",
        "maxPoints": 100,
        "workType": "ASSIGNMENT",
        "dueDate": {
            "year": due_date.year,
            "month": due_date.month,
            "day": due_date.day
        },
        "dueTime": {
            "hours": 23,
            "minutes": 59
        }
    }

    try:
        coursework = service.courses().courseWork().create(
            courseId=course_id, 
            body=assignment_body
        ).execute()
        
        print(f"✅ Assignment created successfully!")
        print(f"ID: {coursework.get('id')}")
        print(f"Link: {coursework.get('alternateLink')}")
        return coursework.get('id')
    
    except Exception as e:
        print(f"❌ Failed to create assignment: {e}")
        return None

# Usage
COURSE_ID = "825125683344"
create_formatted_assignment(COURSE_ID)