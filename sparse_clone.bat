@echo off
@REM Digunakan file submision_get_setup.py untuk clone repo
REM Usage: sparse_clone.bat <repo_url> <folder_name>

SET REPO_URL=%1
SET FOLDER_NAME=%2

IF "%REPO_URL%"=="" (
    echo Error: repo_url tidak diberikan.
    exit /b 1
)
IF "%FOLDER_NAME%"=="" (
    echo Error: folder_name tidak diberikan.
    exit /b 1
)

echo --- Memulai Selective Clone: %FOLDER_NAME% ---

git clone --depth 1 --filter=blob:none --no-checkout %REPO_URL% %FOLDER_NAME%
IF ERRORLEVEL 1 ( echo Gagal: git clone & exit /b 1 )

cd %FOLDER_NAME%
IF ERRORLEVEL 1 ( echo Gagal: masuk folder %FOLDER_NAME% & exit /b 1 )

git sparse-checkout init
IF ERRORLEVEL 1 ( echo Gagal: sparse-checkout init & exit /b 1 )

git sparse-checkout set --no-cone "/*" "!/node_modules/"
IF ERRORLEVEL 1 ( echo Gagal: sparse-checkout set & exit /b 1 )

git checkout
IF ERRORLEVEL 1 ( echo Gagal: checkout & exit /b 1 )

echo --- Clone selesai: %FOLDER_NAME% ---
exit /b 0