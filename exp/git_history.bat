@echo off
setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Usage: git_history ^<filename^>
    exit /b
)

set TARGET=%~1

echo Checking git history for "%TARGET%"
echo.

for /d %%r in (*) do (
    if exist "%%r\.git" (

        cd %%r

        git log --all --pretty=format: --name-only | findstr /I "%TARGET%" >nul

        if !errorlevel! == 0 (
            echo Repo: %%r, FOUND "%TARGET%" in history
        ) else (
            @REM echo Repo: %%r, Not found
        )

        cd ..
    )
)

echo Done.