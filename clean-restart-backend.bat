@echo off
REM Clean Restart Script - Stops all Python processes and starts fresh

echo.
echo ========================================
echo   Clean Backend Restart
echo ========================================
echo.

echo [1/3] Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Waiting for processes to fully stop...
timeout /t 3 /nobreak >nul

echo [3/3] Starting backend with Local LLM...
echo.
set PYTHONIOENCODING=utf-8
set FHIR_LLM_PROVIDER=local_llm
set LOCAL_LLM_URL=http://127.0.0.1:1234
set LOCAL_LLM_MODEL_NAME=openai/gpt-oss-20b
set FHIR_CHATBOT_DEBUG=true

cd backend
call ..\venv\Scripts\activate.bat
python run.py

