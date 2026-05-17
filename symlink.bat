@echo off
:: %1 adalah path target (sumber asli)
:: %2 adalah path link (lokasi shortcut symlink)

:: Cek apakah target adalah folder atau file
if exist "%~1\" (
    :: Jika folder, gunakan /D
    mklink /D "%~2" "%~1"
) else (
    :: Jika file, tanpa flag /D
    mklink "%~2" "%~1"
)