@echo off
chcp 65001
cd /d "%~dp0\.."
.\.venv\Scripts\python.exe src/manga_extractor/main.py
if %errorlevel% neq 0 pause