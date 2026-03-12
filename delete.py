from auth import get_service
def delete_assignment(course_id, coursework_id):
    service = get_service() # Pastikan fungsi get_service Anda sudah siap

    try:
        print(f"Sedang menghapus tugas dengan ID: {coursework_id}...")
        
        service.courses().courseWork().delete(
            courseId=course_id,
            id=coursework_id
        ).execute()
        
        print("✅ Berhasil! Tugas telah dihapus dari Google Classroom.")
        
    except Exception as e:
        if "404" in str(e):
            print("❌ Error: ID Tugas tidak ditemukan.")
        elif "403" in str(e):
            print("❌ Error: Anda tidak punya izin untuk menghapus tugas ini (Mungkin dibuat manual di UI).")
        else:
            print(f"❌ Terjadi kesalahan: {e}")

# --- EKSEKUSI ---
COURSE_ID = "825125683344"
# Masukkan ID tugas yang ingin dihapus (contoh ID dari clone sebelumnya)
TARGET_ID = "851362331527" 
# ⚠️🚨💀 PASTIKAN TARGET_ID SESUAI, PENGHAPUSAN PERMANEN

delete_assignment(COURSE_ID, TARGET_ID)