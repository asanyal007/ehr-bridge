Write-Host "====================================" -ForegroundColor Cyan
Write-Host " Starting Backend with LM Studio" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables for LM Studio
$env:FHIR_LLM_PROVIDER = "local_llm"
$env:LOCAL_LLM_URL = "http://127.0.0.1:1234"
$env:LOCAL_LLM_MODEL_NAME = "openai/gpt-oss-20b"
$env:FHIR_CHATBOT_DEBUG = "true"

Write-Host "✅ FHIR Chatbot configured to use LM Studio" -ForegroundColor Green
Write-Host "   Provider: local_llm"
Write-Host "   URL: $env:LOCAL_LLM_URL"
Write-Host "   Model: $env:LOCAL_LLM_MODEL_NAME"
Write-Host ""

# Navigate to backend directory and start the server
Set-Location backend
..\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8002
