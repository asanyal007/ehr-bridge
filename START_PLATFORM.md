# 🚀 Start AI Data Interoperability Platform Locally

## Quick Start Guide

### ✅ Backend is Already Running!

The backend is currently running at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

You can test it right now:
```bash
curl http://localhost:8000/api/v1/health | python3 -m json.tool
```

---

## 🎨 Frontend Setup

### Prerequisites

You need Node.js and npm installed. Check if you have them:

```bash
node --version
npm --version
```

### Installing Node.js (if needed)

**macOS:**
```bash
# Using Homebrew
brew install node

# Or download from: https://nodejs.org/
```

**Once Node.js is installed:**

```bash
# Navigate to frontend directory
cd /Users/aritrasanyal/EHR_Test/frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will open automatically at **http://localhost:3000**

---

## 🐳 Alternative: Run with Docker (Easiest)

If you don't want to install Node.js, use Docker:

```bash
cd /Users/aritrasanyal/EHR_Test

# Start both backend and frontend
docker-compose up --build

# Access at http://localhost:8000
```

Docker includes everything - no need to install Node.js or Python dependencies!

---

## 📊 Current Status

### ✅ Backend (Running)
- **Port**: 8000
- **Status**: Healthy
- **Database**: SQLite (data/ directory)
- **AI Model**: Sentence-BERT
- **Authentication**: JWT

**Backend Logs:**
```bash
tail -f /Users/aritrasanyal/EHR_Test/backend/backend.log
```

### ⏳ Frontend (Needs Node.js)
- **Port**: 3000 (when started)
- **Tech**: React + Tailwind CSS
- **Features**: Job management, AI analysis, HITL review

---

## 🔧 Managing Services

### Backend Commands

**Check if running:**
```bash
curl http://localhost:8000/
```

**View logs:**
```bash
tail -f backend/backend.log
```

**Stop backend:**
```bash
pkill -f "python3 run.py"
```

**Restart backend:**
```bash
cd backend
python3 run.py > backend.log 2>&1 &
```

### Frontend Commands

**Start frontend:**
```bash
cd frontend
npm start
```

**Build for production:**
```bash
npm run build
```

**Stop frontend:**
Press `Ctrl+C` in the terminal running npm

---

## 🌐 Access URLs

Once both are running:

| Service | URL | Purpose |
|---------|-----|---------|
| **Backend API** | http://localhost:8000 | REST API endpoints |
| **API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **Frontend** | http://localhost:3000 | React UI |
| **Health Check** | http://localhost:8000/api/v1/health | Status monitoring |

---

## 🎯 Quick Test

### Test Backend
```bash
# Get a demo token
curl -X POST http://localhost:8000/api/v1/auth/demo-token | python3 -m json.tool

# Check health
curl http://localhost:8000/api/v1/health | python3 -m json.tool
```

### Test Full Flow (once frontend is running)

1. Open http://localhost:3000
2. You'll be auto-logged in with a demo token
3. Click **"+ Create New Mapping Job"**
4. Paste example schemas:

**Source Schema:**
```json
{
  "patient_first_name": "string",
  "patient_last_name": "string",
  "date_of_birth": "date",
  "medical_record_number": "string"
}
```

**Target Schema:**
```json
{
  "patientFullName": "string",
  "birthDate": "datetime",
  "mrn": "string"
}
```

5. Click **"🧠 Analyze with AI (Sentence-BERT)"**
6. Review AI suggestions
7. Approve mappings
8. Test with sample data!

---

## 🐛 Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
lsof -i :8000
pkill -f "python3 run.py"
```

**Backend not responding:**
```bash
# Check logs
cat backend/backend.log

# Restart
cd backend
python3 run.py > backend.log 2>&1 &
```

### Frontend Issues

**npm not found:**
- Install Node.js from https://nodejs.org/
- Or use Docker: `docker-compose up`

**Port 3000 already in use:**
```bash
# Frontend will automatically try port 3001, 3002, etc.
# Or kill existing process:
lsof -i :3000
```

**Dependencies error:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

## 📦 Docker Option (All-in-One)

**Easiest way - no Node.js or Python setup needed:**

```bash
# From project root
docker-compose up --build

# Access at http://localhost:8000
# Backend and frontend both included!

# Stop
docker-compose down
```

---

## 🎓 Next Steps

Once both services are running:

1. **Explore the UI** at http://localhost:3000
2. **Read API docs** at http://localhost:8000/docs
3. **Try example schemas** from `examples/ehr_hl7_schemas.json`
4. **Review test results** in `TEST_RESULTS.md`
5. **Check deployment guide** in `DEPLOYMENT.md`

---

## 📝 Current Setup Summary

```
✅ Backend:  Running on port 8000
   - Health check: ✅ Healthy
   - Database: ✅ SQLite initialized
   - AI Model: ✅ Ready to load
   - Authentication: ✅ JWT working

⏳ Frontend: Needs Node.js installation
   - Install Node.js: https://nodejs.org/
   - Then run: cd frontend && npm install && npm start
   
🐳 Docker:   Alternative option (includes both)
   - Run: docker-compose up --build
   - No manual setup needed!
```

---

## 💡 Recommendation

**Fastest way to see the full platform:**

1. **Use Docker** (if you have Docker Desktop installed):
   ```bash
   docker-compose up --build
   ```

2. **Or install Node.js** and run frontend separately:
   ```bash
   # Install Node.js from https://nodejs.org/
   cd frontend
   npm install
   npm start
   ```

The backend is already running and ready! Just need to get the frontend up.

---

**Backend Status**: ✅ **RUNNING**  
**Backend URL**: http://localhost:8000  
**Next Step**: Install Node.js and start frontend, OR use Docker

