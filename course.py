from auth import get_service

service = get_service()

# submissions = service.courses().courseWork().studentSubmissions().list(
#     courseId=course_id,
#     courseWorkId=coursework_id
# ).execute()

# service = build("classroom", "v1", credentials=creds)

courses = service.courses().list().execute()

# Course ID
for c in courses.get("courses", []):
    print(c["id"], "-", c["name"])