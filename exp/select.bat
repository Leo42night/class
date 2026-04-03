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
echo Memproses folder: %selectedFolder%
pushd "%selectedFolder%" 2>nul || (
    echo [ERROR] Path "%selectedFolder%" tidak ditemukan.
    pause
    exit /b
)

:: Membuka file spesifik di VS Code
call code "apps\frontend\src\main.tsx"

:: Menjalankan install dan dev
call bun dev
popd