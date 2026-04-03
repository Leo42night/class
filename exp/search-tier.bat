@echo off
setlocal enabledelayedexpansion

:: --- KONFIGURASI ---
set "foldera=apps\frontend"
set "folderb=apps\backend"
set "file=package.json"

echo Mencari ["%foldera%" ATAU "%folderb%"]
echo Jika keduanya tidak ada, mencari "%file%"
echo ----------------------------------------------------------

for /d %%D in (*) do (
    set "found_sub=false"

    :: Cek Folder A
    if exist "%%D\%foldera%" (
        @REM echo [v] Folder %foldera% ditemukan di: %%D
        set "found_sub=true"
    ) else (
        echo [x] Folder %foldera% TIDAK ada di: %%D
    )

    :: Cek Folder B
    if exist "%%D\%folderb%" (
        @REM echo [v] Folder %folderb% ditemukan di: %%D
        set "found_sub=true"
    ) else (
        echo [x] Folder %folderb% TIDAK ada di: %%D
    )

    :: LOGIKA: Jika foldera TIDAK ada DAN folderb TIDAK ada
    if "!found_sub!"=="false" (
        if exist "%%D\%file%" (
            echo [f] Project Standar: %file% ditemukan di root %%D
        ) else (
            @REM echo [-] Folder %%D bukan project yang dikenal.
        )
    )
    echo.
)

echo ----------------------------------------------------------