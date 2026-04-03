@echo off
setlocal enabledelayedexpansion

for /d %%d in (*) do (
    echo.
    echo ---------------------------------------------------
    echo Memproses folder: %%d
    
    if exist "%%d\apps\backend" (
        pushd "%%d\apps\backend"
        
        :: 1. Jalankan server di jendela baru (background)
        :: /B agar tidak membuka window baru, atau biarkan tanpa /B agar terlihat lognya
        echo [>] Menjalankan server...
        start "DevServer_%%d" bun dev
        
        :: 2. Tunggu beberapa detik agar server benar-benar up (misal 5 detik)
        timeout /t 5 /nobreak >nul
        
        :: 3. Jalankan seed
        echo [>] Menjalankan seeding...
        call bun "prisma/seed.ts"
        
        :: 4. Stop server
        :: Kita cari proses 'bun' yang baru saja dijalankan di folder ini
        echo [!] Menghentikan server di %%d...
        
        :: Cara agresif: Kill semua proses bun (Hati-hati jika ada bun lain running)
        :: taskkill /F /IM bun.exe /T >nul 2>&1
        
        :: Cara lebih aman: Gunakan PowerShell untuk kill berdasarkan nama window
        powershell -Command "Stop-Process -Name bun -ErrorAction SilentlyContinue"
        
        popd
    ) else (
        echo [x] Skip: Folder apps\backend tidak ditemukan di %%d
    )
)

echo.
echo Semua folder telah diproses.
pause