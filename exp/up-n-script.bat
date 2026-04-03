@REM update file & run script
@echo off
setlocal enabledelayedexpansion
:: run for /d %D in (*) do echo DATABASE_URL="file:./dev.db" > "%D\apps\backend\.env" 

:: --- KONFIGURASI ---
set "target_path=apps\backend\prisma.config.ts"
:: Gunakan regex escape untuk PowerShell (\")
set "old_text=env\(\"DATABASE_URL\"\)"
set "new_text=process.env.DATABASE_URL"

for /d %%d in (*) do (
    set "file_path=%%d\%target_path%"

    if exist "!file_path!" (
        echo [---] Mengupdate: !file_path!
        
        :: Memanggil PowerShell untuk melakukan replace teks secara aman
        powershell -Command "$path = '!file_path!'; (Get-Content $path) -replace 'env\(\"DATABASE_URL\"\)', 'process.env.DATABASE_URL' | Set-Content $path -Encoding UTF8"
        
        if !errorlevel! equ 0 (
            echo [v] Berhasil diupdate.

            :: Masuk ke folder backend untuk jalankan prisma
            pushd "%%d\apps\backend" 2>nul
            if !errorlevel! equ 0 (
                echo [---] Menjalankan Migrate dan Generate di %%d...
                call bunx --bun prisma migrate dev --name init && call bunx --bun prisma generate
                popd
            ) else (
                echo [x] Gagal masuk ke folder apps\backend di %%d
            )
        ) else (
            echo [x] Gagal mengupdate file di %%d.
        )
    ) else (
        echo [---] Skip: !file_path! (File tidak ditemukan)
    )
)

echo.
echo Semua folder telah diproses.