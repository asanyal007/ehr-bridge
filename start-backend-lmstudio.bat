@echo off
echo ====================================
echo  Starting Backend with LM Studio
echo ====================================
echo.

REM Set environment variables for LM Studio
set FHIR_LLM_PROVIDER=local_llm
set LOCAL_LLM_URL=http://127.0.0.1:1234
set LOCAL_LLM_MODEL_NAME=openai/gpt-oss-20b
set FHIR_CHATBOT_DEBUG=true

echo ✅ FHIR Chatbot configured to use LM Studio
echo    Provider: local_llm
echo    URL: %LOCAL_LLM_URL%
echo    Model: %LOCAL_LLM_MODEL_NAME%
echo.

REM Start the backend
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8002
