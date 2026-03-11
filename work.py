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
    
# 851096517087 - 6# Monorepo (phase 1 & 2)
# 825216058131 - Demografi Peserta Kelas PPWL A
# 846333972549 - #4 Middleware & Validation
# 847559064760 - 5# Project Structure
# 825694572407 - #3 Tailwind CSS
# 818980623852 - 2# Env & Bun.js
# 843182213389 - Tugas 1