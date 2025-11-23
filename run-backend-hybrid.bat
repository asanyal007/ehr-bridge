@echo off
set PYTHONIOENCODING=utf-8
set FHIR_LLM_PROVIDER=local_llm
set LOCAL_LLM_URL=http://127.0.0.1:1234
set LOCAL_LLM_MODEL_NAME=openai/gpt-oss-20b

REM Use SENTENCE-BERT for embeddings (fast and accurate)
REM Use GPT-OSS for reasoning only (explanations and context)
set USE_GPT_OSS=true
set USE_SBERT_EMBEDDINGS=true

echo.
echo   Starting Backend with Hybrid AI Configuration
echo   =============================================
echo   Embeddings: SENTENCE-BERT (fast, accurate)
echo   Reasoning: GPT-OSS (%LOCAL_LLM_MODEL_NAME%)
echo   LLM URL: %LOCAL_LLM_URL%
echo.

cd backend
call ..\venv\Scripts\activate.bat
set PORT=8002
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload

