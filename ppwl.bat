@echo off
:: Ganti path di bawah ini dengan lokasi asli folder project Anda
set PROJECT_DIR=C:\Users\karma\repo\class
set PYTHON_EXE=py

:: Berpindah ke direktori project agar .env dan config terbaca
cd /d "%PROJECT_DIR%"

:: Menjalankan main.py dengan argumen (seperti 'a' atau 'b')
%PYTHON_EXE% main.py %1