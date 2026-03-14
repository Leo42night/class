from auth import get_service
import pandas as pd

service = get_service()

course_id = "825125683344"
coursework_id = "847559064760"
# 847559064760

submissions = service.courses().courseWork().studentSubmissions().list(
    courseId=course_id,
    courseWorkId=coursework_id
).execute()

data = []

for sub in submissions.get("studentSubmissions", []):
    user_id = sub["userId"]
    
    student = service.courses().students().get(
        courseId=course_id,
        userId=user_id
    ).execute()
    
    name = student["profile"]["name"]["fullName"]
    print(f"Memproses {user_id} - {name}...")

    attachments = sub.get("assignmentSubmission", {}).get("attachments", [])
    
    github_username = ""
    github_username_repo = ""

    for att in attachments:
        if "link" in att:
            url = att["link"]["url"]
            if "github.com" in url:
                # Ambil username dari URL
                parts = url.replace("https://github.com/", "").replace(".git", "").split("/")
                # github_username = parts[0]
                github_username_repo = parts[0] + "/" + parts[1] if len(parts) > 1 else parts[0]
                break

    data.append({
        "name": name,
        "github": github_username_repo
    })

# 🔥 CASE-INSENSITIVE SORT
data_sorted = sorted(data, key=lambda x: x["name"].casefold())

# Tampilkan hasil
print("\nHasil:")
for item in data_sorted:
    print(f"{item['name']} | {item['github']}")

# # simpan ke dataframe
# df = pd.DataFrame(data_sorted)

# # simpan ke excel
# df.to_excel("data.xlsx", index=False)