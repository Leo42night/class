@REM pilih folder untuk menjalankan script
@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo       SELECT PROJECT TO RUN (BUN)
echo ==========================================

:: 1. List folder dan simpan ke dalam array
set i=0
for /d %%D in (*) do (
    set /a i+=1
    set "folder!i!=%%D"
    echo [!i!] %%D
)

if %i%==0 (
    echo Tidak ada folder ditemukan di direktori ini.
    pause
    exit /b
)

echo.
:: 2. Minta input user
set /p choice="Pilih nomor folder: "

:: 3. Validasi input dan ambil nama folder
set "selectedFolder=!folder%choice%!"

if "%selectedFolder%"=="" (
    echo Pilihan tidak valid!
    pause
    exit /b
)

:: 4. Eksekusi perintah
echo.

@REM echo Memproses folder: %selectedFolder%
@REM pushd "%selectedFolder%" 2>nul || (
@REM     echo [ERROR] Path "%selectedFolder%" tidak ditemukan.
@REM     pause
@REM     exit /b
@REM )
@REM call bun install

echo Memproses folder: %selectedFolder%\apps\backend
pushd "%selectedFolder%\apps\backend" 2>nul || (
    echo [ERROR] Path "%selectedFolder%\apps\backend" tidak ditemukan.
    pause
    exit /b
)
@REM call bun add @prisma/client-runtime-utils
call bun "prisma\seed.ts"

:: Membuka file spesifik di VS Code
@REM call code "apps\frontend\src\main.tsx"

:: Menjalankan install dan dev
@REM call bunx --bun prisma migrate dev --name init
@REM call bunx --bun prisma generate
popd