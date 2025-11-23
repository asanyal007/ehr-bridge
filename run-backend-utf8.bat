@echo off
REM Set UTF-8 encoding for Python
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

REM Activate virtual environment and run backend
cd backend
call ..\venv\Scripts\activate.bat
python run.py

