@echo off
echo ========================================
echo RESTARTING BACKEND AND VERIFYING ROUTE
echo ========================================
echo.

echo [1] Stopping all Python processes...
taskkill /F /IM python.exe /T 2>nul
timeout /t 2 /nobreak >nul

echo [2] Clearing Python cache...
for /d /r backend %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q backend\*.pyc 2>nul

echo [3] Starting backend on port 8002...
cd backend
set PORT=8002
set AI_ENGINE_MODE=hybrid
set LOCAL_LLM_URL=http://127.0.0.1:1234
set LOCAL_LLM_MODEL_NAME=openai/gpt-oss-20b
set PYTHONIOENCODING=utf-8

start "Backend Server" cmd /k "..\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload"

echo.
echo [4] Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo [5] Verifying route is registered...
cd ..
venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend'); import main; routes = [r.path for r in main.app.routes if hasattr(r, 'path') and hasattr(r, 'methods')]; get_suggestion = [r for r in routes if 'get-suggestion' in r]; print('Routes with get-suggestion:', get_suggestion); print('Total POST routes:', len([r for r in main.app.routes if hasattr(r, 'methods') and 'POST' in r.methods]))"

echo.
echo ========================================
echo BACKEND RESTARTED
echo Check the new window for server logs
echo ========================================
pause

