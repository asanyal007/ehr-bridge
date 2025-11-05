# Quick Start Guide - Healthcare EHR/HL7 AI Data Interoperability Platform

Get the platform running in **5 minutes** with Docker!

## Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose)
- 4GB+ RAM available
- 5GB disk space

## Option 1: Docker (Easiest - Recommended)

### 1. Clone and Start (2 minutes)

```bash
# Clone repository
git clone <repository-url>
cd EHR_Test

# Start with Docker Compose
docker-compose up --build
```

**That's it!** The application will:
- Build the container with Python, Node, and all dependencies
- Download the Sentence-BERT model (~200MB, first time only)
- Initialize SQLite database
- Start FastAPI backend and React frontend

### 2. Access the Application

Open your browser: **http://localhost:8000**

You'll be automatically logged in with a demo token.

### 3. Create Your First Mapping (2 minutes)

1. Click **"+ Create New Mapping Job"**

2. **Source Schema** (Local EHR):
```json
{
  "patient_first_name": "string",
  "patient_last_name": "string",
  "date_of_birth": "date",
  "medical_record_number": "string"
}
```

3. **Target Schema** (Cancer Registry):
```json
{
  "patientFullName": "string",
  "birthDate": "datetime",
  "mrn": "string"
}
```

4. Click **"🧠 Analyze with AI (Sentence-BERT)"**

5. Review the AI-suggested mappings with confidence scores

6. Click **"✓ Approve"** on the mappings you agree with

7. Click **"Finalize and Approve Mappings"**

**Done!** 🎉 Your first EHR/HL7 mapping job is complete.

---

## Option 2: Manual Setup (Development)

### 1. Backend (1 minute)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies (includes Sentence-BERT)
pip install -r requirements.txt

# Start backend
cd backend
python run.py
```

Backend: http://localhost:8000
API Docs: http://localhost:8000/docs

### 2. Frontend (1 minute)

```bash
# Open new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend: http://localhost:3000

---

## Quick Test with Sample Data

Use the provided examples:

### Healthcare Patient Demographics
**Source**: `examples/sample_schemas.json` - "example_1"
**Data**: `examples/sample_data.json` - "example_2"

### HL7 Segments
Try mapping HL7 v2 segments (PID, OBX, etc.) to FHIR resources!

---

## Docker Commands

```bash
# Start application
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Rebuild after code changes
docker-compose up --build

# Remove all data (reset database)
docker-compose down -v
rm -rf data/
```

---

## API Examples

### Get Demo Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/demo-token
```

### Create Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "demo_user_123",
    "sourceSchema": {"first_name": "string", "last_name": "string"},
    "targetSchema": {"full_name": "string"}
  }'
```

### Analyze Schemas
```bash
curl -X POST http://localhost:8000/api/v1/jobs/JOB_ID/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"userId": "demo_user_123"}'
```

---

## What's Next?

1. **Try Real Data**: Use your actual EHR schemas or HL7 message structures

2. **Customize AI**: Update `backend/bio_ai_engine.py` to use BioBERT or ClinicalBERT for better clinical terminology matching

3. **Production Deploy**: See `DEPLOYMENT.md` for production setup

4. **View Docs**: Open `docs/specification.html` for full interactive specification

---

## Troubleshooting

### "Port 8000 already in use"
```bash
# Use different port
docker-compose run -p 8080:8000 app
```

### "Model download slow"
First run downloads ~200MB Sentence-BERT model. Be patient or pre-download:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### "Database error"
```bash
# Reset database
rm -rf data/
docker-compose up
```

---

## Key Features at a Glance

- ✅ **No Cloud Setup** - Everything runs locally in Docker
- ✅ **No API Keys** - Self-contained AI model
- ✅ **No Database Setup** - SQLite auto-initializes
- ✅ **Instant Auth** - Auto-generated JWT tokens
- ✅ **Healthcare-Optimized** - Pre-configured for EHR/HL7

---

**Ready in 5 minutes. No external dependencies. Full AI power.**

For detailed setup and customization, see `SETUP_GUIDE.md`
