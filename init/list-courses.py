from auth import get_service

service = get_service()

courses = service.courses().list().execute()

# Course ID
for c in courses.get("courses", []):
    print(c["id"], "-", c["name"])
    
# 825125683344 - Praktikum PWL 2026 A
# 825266594962 - Praktikum PWL 2026 B