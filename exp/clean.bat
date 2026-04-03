@echo off
setlocal enabledelayedexpansion

echo Menjalankan pembersihan dotenv...
echo ----------------------------------------------------------

for /d %%d in (*) do (
    echo Memproses folder: %%d

    :: 1. Hapus import di prisma.config.ts
    set "prisma_file=%%d\apps\backend\prisma.config.ts"
    if exist "!prisma_file!" (
        echo [a] Cleanup prisma.config.ts
        powershell -NoProfile -Command "$path = '!prisma_file!'; (Get-Content $path) | Where-Object { $_ -notmatch 'import\s+[\"'']dotenv/config[\"''];?' } | Set-Content $path -Encoding UTF8"
    )

    :: 2. Hapus baris "dotenv" di semua package.json (Root, Backend, Frontend)
    :: Kita gunakan array sederhana untuk list file package.json
    for %%f in ("%%d\package.json" "%%d\apps\backend\package.json" "%%d\apps\frontend\package.json") do (
        if exist "%%~f" (
            echo [b] Cleanup %%~f
            powershell -NoProfile -Command "$path = '%%~f'; (Get-Content $path) | Where-Object { $_ -notmatch 'dotenv' } | Set-Content $path -Encoding UTF8"
        )
    )
    echo.
)

echo ----------------------------------------------------------
echo Pembersihan selesai!