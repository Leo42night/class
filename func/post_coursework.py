# Create Coursework ke Classroom
import json
import datetime
from pathlib import Path
from config.cred import get_service_courses

TEMPLATE_DIR = Path("data_tugas")


def _load_templates():
    """Return list of (filename_stem, path) dari semua .json di data_tugas/."""
    if not TEMPLATE_DIR.exists():
        return []
    return sorted(
        [(p.stem, p) for p in TEMPLATE_DIR.glob("*.json")], key=lambda x: x[0]
    )


def _preview_template(data: dict):
    """Tampilkan ringkasan isi template sebelum diposting."""

    due_days = data.get("due_days_from_now", 0)
    due_date = datetime.date.today() + datetime.timedelta(days=due_days)

    due_time = data.get("due_time", {})
    hours = due_time.get("hours", 23)
    minutes = due_time.get("minutes", 59)

    # datetime UTC
    due_dt_utc = datetime.datetime.combine(due_date, datetime.time(hours, minutes))

    # konversi ke UTC+7
    due_dt_local = due_dt_utc + datetime.timedelta(hours=7)

    print(f"\n  Title       : {data.get('title')}")
    print(f"  Max Points  : {data.get('max_points', 100)}")
    print(f"  Due Date    : {due_dt_local.strftime('%Y-%m-%d %H:%M')} UTC+7")

    materials = data.get("materials", [])
    if materials:
        print(f"  Materials   : {len(materials)} item(s)")
        for m in materials:
            link = m.get("link", {})
            print(f"    - {link.get('title', '-')} → {link.get('url', '-')}")

    desc_preview = data.get("description", "")[:80].replace("\n", " ")
    print(
        f"  Description : {desc_preview}{'...' if len(data.get('description', '')) > 80 else ''}"
    )


def _build_body(data: dict) -> dict:
    """Konversi dict template JSON ke format body Classroom API."""
    due_days = data.get("due_days_from_now", 5)
    due_date = datetime.date.today() + datetime.timedelta(days=due_days)
    due_time = data.get("due_time", {"hours": 16, "minutes": 59})

    return {
        "title": data["title"],
        "description": data.get("description", ""),
        "materials": data.get("materials", []),
        "state": "PUBLISHED",
        "maxPoints": data.get("max_points", 100),
        "workType": "ASSIGNMENT",
        "dueDate": {
            "year": due_date.year,
            "month": due_date.month,
            "day": due_date.day,
        },
        "dueTime": {
            "hours": due_time.get("hours", 16),
            "minutes": due_time.get("minutes", 59),
        },
    }


def run_data_tugas(course_id: str):
    """Entry point yang dipanggil dari menu_loop / work_menu."""

    templates = _load_templates()

    if not templates:
        print(f"⚠️  Tidak ada template di folder '{TEMPLATE_DIR}/'.")
        return

    # --- Tampilkan daftar template ---
    print("\n=== Pilih Template Tugas ===")
    for i, (stem, _) in enumerate(templates, start=1):
        print(f"{i}. {stem}")
    print("0. Kembali")

    choice = input(">> ").strip()
    if choice == "0":
        return

    try:
        idx = int(choice) - 1
        stem, path = templates[idx]
    except (ValueError, IndexError):
        print("Pilihan tidak valid.")
        return

    # --- Load & preview ---
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    print(f"\nPreview template '{stem}':")
    _preview_template(data)

    confirm = input("\nPost tugas ini ke Classroom? (y/n) >> ").strip().lower()
    if confirm != "y":
        print("⏭️  Dibatalkan.")
        return

    # --- Post ke Classroom ---
    service = get_service_courses()
    body = _build_body(data)

    try:
        result = (
            service.courses()
            .courseWork()
            .create(courseId=course_id, body=body)
            .execute()
        )

        print("\n✅ Assignment berhasil dibuat!")
        print(f"   ID   : {result.get('id')}")
        print(f"   Link : {result.get('alternateLink')}")

    except Exception as e:
        print(f"❌ Gagal membuat assignment: {e}")
