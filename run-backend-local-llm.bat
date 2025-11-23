@echo off
REM Start Backend with Local LLM Configuration
REM Set UTF-8 encoding for Python
chcp 65001 > nul

REM Configure Local LLM
set FHIR_LLM_PROVIDER=local_llm
set LOCAL_LLM_URL=http://127.0.0.1:1234
set LOCAL_LLM_MODEL_NAME=openai/gpt-oss-20b
set FHIR_CHATBOT_DEBUG=true
set PYTHONIOENCODING=utf-8

echo.
echo ========================================
echo   Starting Backend with Local LLM
echo ========================================
echo.
echo Provider: %FHIR_LLM_PROVIDER%
echo LLM URL: %LOCAL_LLM_URL%
echo Model: %LOCAL_LLM_MODEL_NAME%
echo.

REM Activate virtual environment and run backend
cd backend
call ..\venv\Scripts\activate.bat
python run.py

