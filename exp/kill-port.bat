@echo off
setlocal

set "skip_list=zulfikarnaen"

@REM radika apps/frontend only 
@REM zulfikarnaen apps/backend only

for /f "delims=" %%D in ('dir /b /ad ^| findstr /v "%skip_list%"') do (
    echo Memproses folder: %%D
    pushd "%%D/apps/frontend"
    call bun add kill-port
    popd
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update-kill-port.ps1"