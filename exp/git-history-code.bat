@echo off
setlocal enabledelayedexpansion

:: --- KONFIGURASI ---
set "target_folder=apps\backend\prisma"
set "target_file=db.ts"
set "search_string=import { PrismaClient } from \"@prisma/client\";"

echo Menyeleksi history Git untuk file: %target_file%
echo String dicari: %search_string%
echo ----------------------------------------------------------

for /d %%D in (*) do (
    set "file_path=%%D\%target_folder%\%target_file%"
    
    if exist "!file_path!" (
        pushd "%%D" 2>nul
        if !errorlevel! equ 0 (
            
            :: Cek history git menggunakan git log -S (Pickaxe search)
            :: -S mencari perubahan jumlah kemunculan string tertentu
            git log -S "!search_string!" --oneline "!target_folder!\!target_file!" > temp_git.txt 2>&1
            
            :: Cek apakah file temp_git.txt ada isinya
            for /f %%i in ("temp_git.txt") do set size=%%~zi
            
            if !size! GTR 0 (
                echo [v] DITEMUKAN di history: "%%D"
                REM Opsional: Tampilkan commit hash-nya
                REM type temp_git.txt
            ) else (
                echo [nc] Tidak ada di history: "%%D"
            )
            
            del temp_git.txt
            popd
        ) else (
            echo [x] Gagal akses folder: %%D
        )
    ) else (
        echo [-] Skip: %%D (File tidak ditemukan)
    )
)

echo ----------------------------------------------------------
echo Selesai.
pause