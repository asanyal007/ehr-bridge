# Local LLM Integration for FHIR Chatbot

## Overview

The FHIR Chatbot now supports both **Gemini AI** (cloud-based) and **Local LLM models** (self-hosted) for natural language query processing. This provides flexibility for:
- **Privacy**: Keep all data processing on-premises
- **Cost**: No API fees for local models
- **Compliance**: HIPAA-compliant deployments without cloud dependencies
- **Offline**: Works without internet connection

## Features Added

### 1. Local LLM Client (`backend/local_llm_client.py`)
- OpenAI-compatible API client
- Supports LM Studio, Ollama, LocalAI, and other OpenAI-compatible servers
- Auto-detects available models
- Connection health checking
- Timeout and error handling

### 2. Dual Provider Support
- Seamlessly switch between Gemini and Local LLM
- Environment variable configuration
- Runtime provider switching via API
- Automatic fallback if local LLM unavailable

### 3. New API Endpoints

#### Get Current Provider
```http
GET /api/v1/chat/llm/provider
```

**Response:**
```json
{
  "success": true,
  "provider": "local_llm",
  "local_llm_url": "http://127.0.0.1:1234",
  "model_name": "llama-3-70b",
  "available": true
}
```

#### Switch Provider
```http
POST /api/v1/chat/llm/provider
Content-Type: application/json

{
  "provider": "local_llm"
}
```

**Response:**
```json
{
  "success": true,
  "provider": "local_llm",
  "message": "Switched to local_llm provider"
}
```

#### List Available Models
```http
GET /api/v1/chat/llm/models
```

**Response:**
```json
{
  "success": true,
  "base_url": "http://127.0.0.1:1234",
  "models": [
    {
      "id": "llama-3-70b",
      "object": "model",
      "created": 1234567890
    }
  ],
  "count": 1
}
```

## Configuration

### Environment Variables

Add to your `.env` file or set as environment variables:

```bash
# Choose provider: 'gemini' or 'local_llm'
FHIR_LLM_PROVIDER=local_llm

# Local LLM server URL (default: http://127.0.0.1:1234)
LOCAL_LLM_URL=http://127.0.0.1:1234

# Optional: Enable debug logging
FHIR_CHATBOT_DEBUG=true
```

### Using Gemini (Default)
```bash
FHIR_LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key-here
```

### Using Local LLM
```bash
FHIR_LLM_PROVIDER=local_llm
LOCAL_LLM_URL=http://127.0.0.1:1234
```

## Supported Local LLM Servers

### 1. LM Studio
- **Download**: https://lmstudio.ai
- **Default Port**: 1234
- **Setup**:
  1. Download and install LM Studio
  2. Download a model (recommend: Llama 3, Mistral, or Phi-3)
  3. Go to "Local Server" tab
  4. Click "Start Server"
  5. Server runs on http://127.0.0.1:1234

### 2. Ollama
- **Download**: https://ollama.ai
- **Default Port**: 11434
- **Setup**:
  ```bash
  # Install Ollama
  curl https://ollama.ai/install.sh | sh
  
  # Pull a model
  ollama pull llama3
  
  # Set environment variable
  export LOCAL_LLM_URL=http://127.0.0.1:11434
  ```

### 3. LocalAI
- **GitHub**: https://github.com/go-skynet/LocalAI
- **Docker**:
  ```bash
  docker run -p 8080:8080 localai/localai:latest
  export LOCAL_LLM_URL=http://127.0.0.1:8080
  ```

### 4. text-generation-webui (oobabooga)
- **GitHub**: https://github.com/oobabooga/text-generation-webui
- Enable OpenAI-compatible API extension
- Default port: 5000
- Set: `LOCAL_LLM_URL=http://127.0.0.1:5000`

## Recommended Models

For healthcare/clinical data queries, these models work well:

| Model | Size | Performance | Best For |
|-------|------|-------------|----------|
| **Llama 3 70B** | 70B | Excellent | Best accuracy, requires powerful GPU |
| **Llama 3 8B** | 8B | Very Good | Good balance, works on consumer GPU |
| **Mistral 7B** | 7B | Good | Fast responses, good for queries |
| **Phi-3** | 3.8B | Good | Lightweight, runs on CPU |
| **CodeLlama 34B** | 34B | Excellent | Great for structured data queries |

## Quick Start

### Step 1: Start Local LLM Server

**Using LM Studio** (Easiest):
1. Download LM Studio from https://lmstudio.ai
2. Download a model (e.g., "meta-llama-3-8b-instruct")
3. Go to "Local Server" tab → Start Server
4. Verify it's running at http://127.0.0.1:1234

### Step 2: Configure Backend

Edit `.env` or set environment variables:
```bash
FHIR_LLM_PROVIDER=local_llm
LOCAL_LLM_URL=http://127.0.0.1:1234
```

### Step 3: Restart Backend
```bash
.\run-backend-utf8.bat
```

### Step 4: Verify Connection

Check backend logs for:
```
[OK] Local LLM Client initialized: http://127.0.0.1:1234 (model: llama-3-8b)
[OK] FHIR Chatbot using Local LLM at http://127.0.0.1:1234
[OK] FHIR Chatbot Service initialized with local_llm provider
```

### Step 5: Test the Chatbot

Open FHIR Chatbot in the UI and ask:
```
How many patients do we have?
```

## API Endpoints Reference

### Local LLM Server Endpoints (Used by Backend)

The backend uses these OpenAI-compatible endpoints on your local server:

```http
GET /v1/models
POST /v1/chat/completions
POST /v1/completions
POST /v1/embedding
```

## Troubleshooting

### Issue: "Local LLM server not available"

**Solution**:
1. Verify server is running:
   ```bash
   curl http://127.0.0.1:1234/v1/models
   ```
2. Check the port number matches
3. Ensure firewall allows localhost connections
4. Check server logs for errors

### Issue: "Request timed out"

**Solution**:
1. Model might be too large for your hardware
2. Try a smaller model (e.g., Phi-3 instead of Llama 70B)
3. Increase timeout in `local_llm_client.py` (default: 60s)

### Issue: "Fallback to Gemini"

**Cause**: Local LLM server couldn't be reached

**Solution**:
1. Start the local LLM server
2. Check `LOCAL_LLM_URL` environment variable
3. System will use Gemini until local LLM is available

### Issue: Poor Response Quality

**Solution**:
1. Try a larger/better model
2. Ensure model is fully loaded (check LM Studio)
3. Adjust temperature in `local_llm_client.py` (default: 0.7)

## Performance Comparison

| Aspect | Gemini AI | Local LLM (Llama 3 8B) | Local LLM (Llama 3 70B) |
|--------|-----------|------------------------|-------------------------|
| **Speed** | 1-3 seconds | 2-5 seconds (GPU) | 5-15 seconds |
| **Accuracy** | Excellent | Very Good | Excellent |
| **Privacy** | Cloud | Local | Local |
| **Cost** | API fees | Hardware | Hardware |
| **Internet** | Required | Not required | Not required |
| **Setup** | API key only | Model download | Powerful GPU needed |

## Hardware Requirements

### Minimum (for Phi-3 or small models):
- CPU: Modern multi-core processor
- RAM: 8GB
- GPU: Optional (will use CPU)
- Storage: 5GB for model

### Recommended (for Llama 3 8B):
- CPU: Recent multi-core (Intel i7/AMD Ryzen 7+)
- RAM: 16GB
- GPU: NVIDIA RTX 3060 12GB or better
- Storage: 10GB for models

### Optimal (for Llama 3 70B):
- CPU: High-end multi-core
- RAM: 64GB+
- GPU: NVIDIA RTX 4090 24GB or A100
- Storage: 50GB+ for models

## Security Considerations

### Advantages of Local LLM:
✅ All data stays on-premises  
✅ No data sent to external APIs  
✅ HIPAA-compliant (when properly configured)  
✅ No API key management  
✅ Offline operation  

### Requirements:
- Secure the local LLM server (localhost only or proper auth)
- Ensure model files are from trusted sources
- Keep local LLM software updated
- Monitor server logs for unusual activity

## Migration Guide

### From Gemini to Local LLM:

1. **Install LM Studio** and download a model
2. **Start the server**
3. **Update configuration**:
   ```bash
   export FHIR_LLM_PROVIDER=local_llm
   ```
4. **Restart backend**
5. **Test queries** - responses should work the same

### From Local LLM to Gemini:

1. **Update configuration**:
   ```bash
   export FHIR_LLM_PROVIDER=gemini
   export GEMINI_API_KEY=your-key
   ```
2. **Restart backend**

### Runtime Switching (No Restart):

Use the API endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/chat/llm/provider \
  -H "Content-Type: application/json" \
  -d '{"provider": "local_llm"}'
```

## Cost Analysis

### Gemini AI:
- **Free Tier**: 60 requests/minute
- **Paid**: ~$0.00025 per 1K characters
- **Monthly** (1000 queries): ~$5-20

### Local LLM:
- **Initial**: $0 (using existing hardware) to $2000+ (new GPU)
- **Operating**: Electricity only (~$5-20/month)
- **Models**: Free (open-source)
- **Break-even**: 1-6 months depending on usage

## Files Modified

1. **`backend/local_llm_client.py`** - NEW: Local LLM client implementation
2. **`backend/fhir_chatbot_service.py`** - Updated: Dual provider support
3. **`backend/main.py`** - Updated: New API endpoints for provider management
4. **`LOCAL_LLM_INTEGRATION_GUIDE.md`** - NEW: This documentation

## Testing

### Test Local LLM Connection:
```bash
curl http://127.0.0.1:1234/v1/models
```

### Test Chat Query:
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many patients do we have?"}'
```

### Check Current Provider:
```bash
curl http://localhost:8000/api/v1/chat/llm/provider
```

## Status

✅ **Local LLM client implemented**  
✅ **Dual provider support added**  
✅ **API endpoints for provider management**  
✅ **Auto-detection of models**  
✅ **Fallback mechanism**  
✅ **Documentation complete**  

## Date Added
November 22, 2025

---

**The FHIR Chatbot now supports both cloud (Gemini) and local LLM models for maximum flexibility!**

