@echo off
setlocal

for /d %%d in (*) do (
    echo Memproses folder: %%d
    pushd "%%d"
    call bun install
    popd
)

echo.
echo Semua folder telah diproses.
pause