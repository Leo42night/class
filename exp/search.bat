@REM Cari baris kode yang tidak ada pada target file (filder dir tertentu)
@echo off
setlocal enabledelayedexpansion

@REM set "folder=apps\frontend"
@REM set "file=tsconfig.json"
@REM references tsconfig.app.json

set "folder=apps\frontend"
set "file=tsconfig.app.json"
@REM path

set "skip_list=audy prilia radika rito salsabila syafira zulfikarnaen"


@REM :: Handle jika skip_list kosong
if "%skip_list%"=="" set "skip_list=DUMMY_UNUSED_SKIP"

set /p search_string="Masukkan potongan kode: "

echo Menyeleksi "%folder%\%file%" (filtered) yang TIDAK ada kode: "%search_string%"
echo ----------------------------------------------------------


for /f "delims=" %%D in ('dir /b /ad ^| findstr /v "%skip_list%"') do (
    set "target_file=%%D\%folder%\%file%"
    set "count=0"

    if exist "%%D\%folder%" (
        if exist "!target_file!" (
            REM Trik: Masukkan search_string ke file sementara untuk dibaca findstr
            REM Ini menghindari masalah parsing tanda kutip di baris perintah
            for /f %%C in ('findstr /l /c:"!search_string!" "!target_file!" 2^>nul ^| find /c /v ""') do set "count=%%C"
            
            if !count! GTR 1 (
                echo [d]  DUPLIKAT (!count! kali^) : "%%D"
            ) else (
                if !count! EQU 1 (
                    echo [v]  OKE (1 kali^)        : "%%D"
                ) else (
                    echo [nc] KOSONG (0 kali^)     : "%%D"
                )
            )
        ) else (
            echo [nf] FILE TIDAK ADA      : "%%D"
        )
    ) else (
        echo [x/] FOLDER TIDAK ADA    : "%%D"
    )
)

echo ----------------------------------------------------------