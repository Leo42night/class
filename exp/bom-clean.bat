@echo off
setlocal enabledelayedexpansion

echo Menghapus BOM (Fix SyntaxError) pada semua apps\frontend\package.json...
echo ----------------------------------------------------------------------

for /d %%D in (*) do (
    @REM set "target=%%D\apps\frontend\package.json"
    @REM set "target=%%D\apps\backend\package.json"
    set "target=%%D\package.json"
    
    if exist "!target!" (
        echo [!] Membersihkan: !target!
        
        :: Menggunakan .NET WriteAllLines untuk memastikan file disimpan sebagai UTF-8 Tanpa BOM
        powershell -NoProfile -Command "$path = '!target!'; $content = Get-Content $path; [System.IO.File]::WriteAllLines($path, $content)"
        
        if !errorlevel! equ 0 (
            echo [v] Berhasil.
        ) else (
            echo [x] Gagal memproses %%D.
        )
    )
)