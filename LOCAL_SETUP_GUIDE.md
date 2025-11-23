# Local Development Setup Guide

## Current Status
✅ MongoDB is now running in Docker (accessible at `localhost:27017`)

## What You Need to Install

### 1. Install Python 3.10+
**Download from**: https://www.python.org/downloads/

During installation:
- ✅ Check "Add Python to PATH"
- ✅ Check "Install pip"

### 2. Install Node.js 18+ (For frontend development)
**Download from**: https://nodejs.org/

Choose the LTS version.

## Quick Start After Installation

### Step 1: Install Python Dependencies
```bash
cd backend
pip install -r ../requirements.txt
```

### Step 2: Set Environment Variables
Create a `.env` file in the backend directory:
```bash
JWT_SECRET_KEY=your-secret-key-for-local-dev
DATABASE_PATH=../data/interop.db
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=ehr
GEMINI_API_KEY=your-gemini-key-or-leave-empty
```

### Step 3: Start Backend
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables auto-restart on code changes (great for debugging!)

### Step 4: Frontend (Choose One)

**Option A: Use Pre-built Frontend** (Faster)
The backend will serve the pre-built React frontend automatically from `frontend/build`

**Option B: Run Frontend in Development Mode** (Better for debugging)
```bash
cd frontend
npm install
npm start
```
Frontend will run on http://localhost:3000

## Debugging the Slow Ingestion Screen

### Enable Verbose Logging

Add this to `backend/main.py` at the top:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Add Performance Timing

I'll add timing measurements to the slow endpoints to identify bottlenecks.

### Check MongoDB Performance

```bash
docker logs ehr-mongodb-dev -f
```

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Port 27017 already in use"
```bash
docker stop ehr-mongodb-dev
docker start ehr-mongodb-dev
```

### "Permission denied on data/"
```bash
mkdir -p data
chmod 777 data
```

## Stop Local MongoDB
```bash
docker stop ehr-mongodb-dev
docker rm ehr-mongodb-dev
```

## Benefits of Local Development

1. ✅ **Faster iteration** - No container rebuilds
2. ✅ **Better debugging** - Direct access to Python debugger
3. ✅ **Hot reload** - Code changes apply instantly
4. ✅ **Full logging** - See all console output in real-time
5. ✅ **IDE integration** - Breakpoints, variable inspection, etc.



