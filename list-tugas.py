from auth import get_service

def list_and_check_permissions(course_id):
    service = get_service()
    
    print(f"--- Assignment Audit for Course: {course_id} ---")
    results = service.courses().courseWork().list(courseId=course_id).execute()
    coursework = results.get('courseWork', [])

    if not coursework:
        print("No assignments found in this course.")
        return

    # Table Header
    print(f"{'Title':<30} | {'ID':<15} | {'Can Edit?':<10}")
    print("-" * 60)

    for item in coursework:
        title = item.get('title', 'No Title')[:28]
        work_id = item.get('id')
        
        # This is the key field:
        can_edit = item.get('associatedWithDeveloper', False)
        
        status = "✅ YES" if can_edit else "❌ NO (UI Created)"
        print(f"{title:<30} | {work_id:<15} | {status}")

# Usage
# 825125683344 - Praktikum PWL 2026 A
# 825266594962 - Praktikum PWL 2026 B
# list_and_check_permissions("825125683344")
list_and_check_permissions("825266594962")
