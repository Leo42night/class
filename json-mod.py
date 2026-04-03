import json

# 1. Load the JSON file
with open("question_clean.json", "r") as file:
    data = json.load(file)

for item in data:
    if "points" in item:
        if item["points"] == 5:
            item["points"] = 15
        elif item["points"] == 3:
            item["points"] = 10
        elif item["points"] == 1:
            item["points"] = 5

# menghitung total poins
total_points = 0
for item in data:
    if "points" in item:
        total_points += item["points"]

print(f"Total points: {total_points}")

# 2. Filter dan bersihkan string di tiap object
for item in data:
    if "question" in item:
        # Memotong teks sebelum bagian \n```
        # Jika tidak ditemukan, teks tetap utuh
        item["question"] = item["question"].split("\n```")[0]

# 3. Save as a new JSON list file
with open("question_clean.json", "w") as file:
    json.dump(data, file, indent=4)
