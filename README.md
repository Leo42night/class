# API Classroom
Untuk pengajar dalam mengelola classroom. Post tugas. Ambil data tugas (link Github, File lain-lain). Upload score ke spreadsheet & classroom.

> integrasi ke Google Spreadsheet untuk laporan dan menyimpan catatan nilai.

---
> 🚨 Versi ini dibuat dengan asumsi Teacher mengajar 1 course dengan >1 sub course. contoh: class **ppwl-a** & **ppwl-b**. 
- ✅ Kode ini cocok untuk 1 course &  subcourse lebih dari 1
- 🚨 Perlu penyesuaian _penambahan_ kode untuk course lebih dari 1
- 🚨 Perlu penyesuaian _pengurangan_ kode jika tidak ada sub-course
---

Stuktur:
```bash
main.py # CLI App yang punya beberapa fungsi (perlu setup config\env.py)
func/ # fitur-fitur yang diakses main.py
utils/ # fungsi tunggal untuk menjalankan perintah khusus & development testing.
data_score/ # daftar data *.txt untuk fitur scoring.py 
data_tugas/ # daftar data *.json template tugas untuk fitur post_coursework.py 
```

## Installation
```bash
pip install python-dotenv google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```
### Oauth Client
- buat proyek di google cloud console
- aktifkan API **Classroom** & **Sheet**
- buat Oauth Desktop Type (save as **credentials.json**)
```
https://www.googleapis.com/auth/classroom.courses.readonly
https://www.googleapis.com/auth/classroom.student-submissions.students.readonly
https://www.googleapis.com/auth/classroom.rosters.readonly
https://www.googleapis.com/auth/classroom.coursework.students
```
- Tambahkan scope ini, ke dalam:
```
APIs & Services
  -> Oauth consent screen 
  -> Data Access -> Add or Remove scope
  -> paste-kan ke input text area di bagian "Manually add scopes"
```

### Service Account
format credentials (format Service Account) untuk edit Spreadsheet:
> **IAM & Admin → Service Accounts**
Setelah dibuat Service Accounts, masuk:
```
Keys
  → Add Key
  → Create new key
  → JSON
```
Save as **service-account.json**
```json
{
  "type": "service_account",
  "project_id": "my-project",
  "private_key_id": "xxxxxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n....\n-----END PRIVATE KEY-----\n",
  "client_email": "my-service@my-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```
📩 **Tambahkan email** ke file spreadsheet.

Setelah di-setup kita dapat akses Classroom & Spreadsheet.

## **Publish Tugas**
Deskripsi tugas dapat di format pakai tools:
- [Bold Text](https://www.namecheap.com/visual/font-generator/bold-text/)
- [Bullet Point](https://emojidb.org/bullet-point-emojis)

Setelah buat kode tugas di `data_tugas`/{nama_tugas}.json, ikuti `template_coursework.json`. **PASTIKAN** di .json, due time ditulis -7 hour dari waktu sebenarnya (UTC+7). misal 23:59 (UTC+7) jadi 16:59 (UTC).

Kirimkan post lewat fitur di **Main Menu**.

## Main Menu
- run `py config/list-courses.py`, ambil course_id,name,course_code courses masukkan ke `config/courses.txt`
- masukkan **course_code**, **spreadsheet_id**, & **n_students** (jumlah siswa di class tersebut) ke CLASS_CONFIG di main.py
- run `py main.py <course_code>` anda dapat memilih:
  - `Lihat Work` -> pilih Work -> opsi: 
    - **Ambil Github -> Clone & Spreadsheet**
    - **Assign Score & Notes -> Sheet & Classroom**
  - `Post Tugas Baru` -> pilih template tugas.

### Ambil Github -> Clone & Spreadsheet
Fitur untuk mengambil link repo yang dikirim di Work (tugas) yg dipilih.
Sebelum memilih menu ini, siapkan dulu:
> di **google spreadsheet** rekap:
1. buat tab "{class_code}{tugas_ke}"
2. masukkan nama dari classroom -> student, ke kolom **Name in Classroom** (urutan header: `No`, `Name in Classroom`,	`Repo`,	`Notes`,	`Score`	`Codename`). Pasangkan dengan codename (nama unik Ascending untuk folder repo) nya. Data `Name in Classroom` di B2:B{N_STUDENT+1}, dan `Codename` di F2:F{N_STUDENT+1}

> di **CLI main.py** \<code\> -> `Lihat Work` -> pilih Work -> opsi:
3. Pilih menu **Ambil Github -> Clone & Spreadsheet**, masukkan nilai **Tugas ke:** dengan angka `tugas_ke` pada nama tab di spreadsheet.

Perintah akan menghasilkan:
  - `clone.txt` (Gunakan untuk run clone tiap repo submisi, dinilai di local. Selanjutnya anda dapat membuat file `*-score.txt` & lanjut menu **assign ke Spreadsheet & Classroom**)
  - Kolom repo di Spreadsheet akan terisi value & link nya.

### Assign Score & Notes -> Sheet & Classroom
Logika kode seperti ini:
  - Ikuti template `{class_code}-{tugas_ke}-score.txt`.
  - Ambil nilai minus yang ada dibawah tiap **`>` codename** (tiap nama ditemukan, ambil score & notesnya). 
  - Kelompokkan berdasarkan **codename**, masukkan ke spreadsheet & classroom (Classroom hanya dapat di assign score untuk Tugas yang menggunakan API. Lihat: [Publish Tugas](#publish-tugas))