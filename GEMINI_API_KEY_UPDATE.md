# 📝 Where to Update Gemini API Key

## ✅ Primary Location (Recommended)

**File:** `.env` (in the project root)

```bash
# Edit this file directly
nano .env

# Or update via command line:
sed -i '' 's/GEMINI_API_KEY=.*/GEMINI_API_KEY=YOUR_NEW_API_KEY/' .env
```

**Current value:** `GEMINI_API_KEY=AIzaSyCwfd_DHnKMYOWMbqX5VVTmyRNBv-Ni5vI`

This is the **recommended** location because:
- The Docker container reads from this file via `docker-compose.yml`
- Environment variables are the standard way to manage secrets
- No code changes needed after updating

---

## 🔧 Fallback Locations (Updated as Defaults)

These files have hardcoded fallback values in case the environment variable is not set. **You don't need to update these unless you're not using Docker or the .env file.**

### 1. `backend/fhir_chatbot_service.py` (Line 221)
```python
self.api_key = api_key or os.getenv("GEMINI_API_KEY", "AIzaSyCwfd_DHnKMYOWMbqX5VVTmyRNBv-Ni5vI")
```

### 2. `backend/gemini_ai.py` (Line 24)
```python
self.api_key = api_key or os.getenv("GEMINI_API_KEY", "AIzaSyCwfd_DHnKMYOWMbqX5VVTmyRNBv-Ni5vI")
```

### 3. `backend/omop_vocab.py` (Line 41)
```python
self.gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCwfd_DHnKMYOWMbqX5VVTmyRNBv-Ni5vI")
```

---

## 🚀 How to Apply Changes

### Option 1: Update .env file only (Recommended)
```bash
# 1. Update .env file
echo "GEMINI_API_KEY=YOUR_NEW_API_KEY" >> .env

# 2. Restart the application
./stop.sh
./start.sh
```

### Option 2: Update .env and rebuild (if using Docker)
```bash
# 1. Update .env file
sed -i '' 's/GEMINI_API_KEY=.*/GEMINI_API_KEY=YOUR_NEW_API_KEY/' .env

# 2. Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Option 3: Update code defaults (if not using Docker)
Update all three Python files listed above, then restart the backend.

---

## ✅ Verification

After updating, test the API key:

```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many patients do we have?"}'
```

If you see an error about "API key not valid", the key hasn't been picked up yet. Try:
- Restarting the backend: `docker-compose restart app`
- Checking logs: `docker-compose logs app | grep -i gemini`
- Verifying .env is loaded: `docker-compose exec app env | grep GEMINI_API_KEY`

---

## 📋 Summary

**For normal use:** Update `.env` file only ✅

**For development:** Update `.env` + fallback defaults in code files

**Current API Key:** `AIzaSyCwfd_DHnKMYOWMbqX5VVTmyRNBv-Ni5vI` (as of latest update)

