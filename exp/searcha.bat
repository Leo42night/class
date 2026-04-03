@REM search line in file, show list dir yang ada
@echo off
setlocal enabledelayedexpansion

:: --- KONFIGURASI ---
set /p search_string="Masukkan potongan kode yang DICARI: "
@REM set "target_file=package.json"
@REM ependen
@REM set "target_file=apps\backend\prisma\schema.prisma" 
@REM url
set "target_file=dev.db" 
@REM url
:: -------------------

echo Menyeleksi folder yang MEMILIKI kode: "%search_string%"
echo ----------------------------------------------------------

:: Loop melalui semua direktori di folder saat ini
for /d %%D in (*) do (
    
    :: Cek apakah file target ada di dalam subfolder tersebut
    if exist "%%D\%target_file%" (
        
        :: Cari string di dalam file tersebut secara silent
        findstr /c:"%search_string%" "%%D\%target_file%" >nul 2>&1
        
        :: Jika errorlevel adalah 0, berarti string DITEMUKAN
        if !errorlevel! equ 0 (
            echo [v] DITEMUKAN di folder: %%D
        )
    )
)

echo ----------------------------------------------------------
pause