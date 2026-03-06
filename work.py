from auth import get_service

service = get_service()

course_id = "825125683344"
# coursework_id = "845616427806"

# 825266594962 - Praktikum PWL 2026 B
# 825125683344 - Praktikum PWL 2026 A

coursework = service.courses().courseWork().list(
    courseId=course_id
).execute()

for work in coursework.get("courseWork", []):
    print(work["id"], "-", work["title"])