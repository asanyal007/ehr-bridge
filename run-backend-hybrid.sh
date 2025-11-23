#!/bin/bash

export PYTHONIOENCODING=utf-8
export FHIR_LLM_PROVIDER=local_llm
export LOCAL_LLM_URL=http://127.0.0.1:1234
export LOCAL_LLM_MODEL_NAME=openai/gpt-oss-20b

# Use SENTENCE-BERT for embeddings (fast and accurate)
# Use GPT-OSS for reasoning only (explanations and context)
export USE_GPT_OSS=true
export USE_SBERT_EMBEDDINGS=true

echo ""
echo "  Starting Backend with Hybrid AI Configuration"
echo "  ============================================="
echo "  Embeddings: SENTENCE-BERT (fast, accurate)"
echo "  Reasoning: GPT-OSS ($LOCAL_LLM_MODEL_NAME)"
echo "  LLM URL: $LOCAL_LLM_URL"
echo ""

cd backend
source ../venv/bin/activate
export PORT=8002
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload

