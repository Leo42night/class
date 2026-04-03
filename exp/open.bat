@echo off
setlocal

for /d %%d in (*) do (
    if exist "%%d\public\css\style.css" (
        echo Opening %%d\public\css\style.css
        code "%%d\public\css\style.css"
    )
)

echo Done.
pause