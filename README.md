# EHR AI Interoperability Platform

A full‑stack, AI‑assisted data interoperability platform for healthcare that ingests CSV/HL7 v2, transforms to FHIR and OMOP, normalizes clinical terminology, and provides a natural‑language chatbot for querying FHIR data.

- Backend: FastAPI (Python)
- Frontend: React (SPA, built and served by FastAPI)
- Datastores: MongoDB (FHIR store, HL7 staging, OMOP target), SQLite (config, jobs, mappings, caches, vocab subset)
- AI: Google Gemini (prompting, table/resource prediction, NLU), Sentence‑BERT (Bio/Clinical models) for semantic matching
- Auth: JWT (permissive by default for local/dev)
- Containerization: Docker + Docker Compose

---

## Key Features

- AI‑assisted mapping and transformation
  - CSV schema inference
  - FHIR resource prediction and mapping suggestions (HITL review)
  - OMOP table prediction and concept normalization with confidence scores
- HL7 v2 mastery
  - Grammar‑based parsing to columnar
  - Columnar → HL7 v2 synthesis
  - Structural error handling and DLQ for failed records
- Ingestion engine
  - Source connectors (CSV, MongoDB) → FHIR store (MongoDB, `fhir_*` collections)
  - Real‑time pipeline orchestration with approved mappings
  - Failed records viewer
- OMOP pipeline
  - Predict table → Normalize Concepts → Preview → Persist to Mongo (`omop_*` collections)
  - Deterministic ID services (`person_id`, `visit_occurrence_id`)
- FHIR Data Chatbot
  - Natural language → MongoDB query (Gemini)
  - Query validator and sanitizer
  - Plain‑text answer synthesis with RAG
- UX
  - ADF‑inspired connector configuration & schema view
  - Searchable dropdowns for HITL mapping with FHIR path support
  - Tailwind styling, toasts, progressive disclosure

---

## Repository Structure

```text
backend/                  # FastAPI app, engines, services
frontend/                 # React SPA (built and served by backend)
data/                     # SQLite db, vocab seeds (volume-mounted in compose)
sample_data_*.csv         # Sample CSVs
Dockerfile                # Multi-stage build (frontend + backend)
docker-compose.yml        # App + MongoDB services
start.sh | stop.sh        # One-click run scripts (macOS)
logs.sh | status.sh       # Utility scripts
build-package.sh          # Package builder (tarball with scripts + env)
README.md                 # This file
```

---

## Prerequisites

- Docker Desktop (macOS/Windows/Linux)
- 6–8 GB RAM available to Docker recommended

---

## Quick Start (Docker Compose)

1) Create the `.env` file (root):

```bash
cp .env .env.backup 2>/dev/null || true
cat > .env << 'ENV'
# JWT Secret Key for authentication
JWT_SECRET_KEY=change-this-to-a-secure-random-string

# Google Gemini API Key for AI features
GEMINI_API_KEY=your-gemini-api-key

# MongoDB Configuration
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB=ehr

# Feature flags
SHOW_OMOP=true
ENV
```

2) Start with scripts (recommended on macOS):

```bash
./start.sh
```

Or with raw compose:

```bash
docker-compose up -d --build
```

3) Open the app:

- Backend/UI: http://localhost:8000 (FastAPI serves the React build)
- Alternative UI: http://localhost:3000 (if you proxy/serve separately)
- MongoDB: mongodb://localhost:27017

4) View logs:

```bash
./logs.sh
# or
docker-compose logs -f
```

5) Stop:

```bash
./stop.sh
# or
docker-compose down
```

---

## Environment Variables

- `JWT_SECRET_KEY`: Secret for signing JWTs
- `GEMINI_API_KEY`: Google Gemini API key (required for AI features)
- `MONGO_HOST`, `MONGO_PORT`, `MONGO_DB`: Mongo connection
- `SHOW_OMOP`: Feature flag for OMOP UI endpoints (default `true`)
- Optional: `FHIR_CHATBOT_DEBUG=true` to enable verbose chatbot logs

See `GEMINI_API_KEY_UPDATE.md` for detailed API key update steps.

---

## Build & Run Flow (What happens under the hood)

- Docker builds frontend (React) and copies the production build into the backend image
- FastAPI serves API under `/api/v1/*` and the React SPA for non‑API routes
- MongoDB runs as a service with a named volume for persistence
- SQLite file `data/interop.db` is created/maintained by the backend

---

## Core Workflows

### 1) CSV → FHIR Ingestion

- Upload CSV → infer schema
- AI suggests FHIR resource + mappings (HITL to approve)
- Create/approve mapping → Start ingestion job
- Records land in MongoDB `fhir_*` collections
- Failed records visible in UI (with reasons)

### 2) FHIR → OMOP Modeling

- From an ingestion job, open Data Model
- Predict OMOP table (Gemini + heuristics)
- Normalize concepts (lookup → S‑BERT → Gemini; with confidence scores)
- Preview rows → Persist to `omop_<TABLE>` collections in MongoDB

### 3) FHIR Data Chatbot

- Ask questions in plain English (e.g., “Show me female patients”)
- Gemini translates to a safe MongoDB query
- Results synthesized to plain‑text answers

---

## Important API Endpoints (v1)

FHIR Chatbot

```http
POST /api/v1/chat/query
Body: { "question": "Show me female patients" }
Resp: { answer, query_used, results_count, response_time }

POST /api/v1/chat/reset
Body: { conversation_id }
```

OMOP Modeling

```http
POST /api/v1/omop/predict-table
Body: { sourceSchema?, jobId? } → { table, confidence, rationale }

POST /api/v1/omop/preview
Body: { jobId, mappingId?, table?, limit } → { rows, fieldCoverage }

POST /api/v1/omop/persist
Body: { jobId, mappingId?, table?, rows } → { insertedCountsByTable }

POST /api/v1/omop/persist-all
Body: { jobId, table?, dry_run? } → { insertedCountsByTable }

GET  /api/v1/omop/concepts/search?query=...&domain=...
 → [{ concept_id, concept_name, vocabulary_id, domain_id, standard_concept }]

POST /api/v1/omop/concepts/normalize
Body: { values[], domain, vocabulary?, job_id?, target_table? } → suggestions

PUT  /api/v1/omop/concepts/approve
Body: { jobId, field, mapping: { sourceValue → concept_id, ... } }

POST /api/v1/omop/ids/person
POST /api/v1/omop/ids/visit
```

Ingestion & HL7/FHIR (representative)

```http
GET  /api/v1/ingestion/jobs
POST /api/v1/ingestion/jobs
POST /api/v1/ingestion/jobs/{id}/start
GET  /api/v1/ingestion/jobs/{id}/records
GET  /api/v1/omop/compatible-jobs
```

---

## Scripts (macOS)

```bash
./start.sh            # Build + run all services
./stop.sh             # Stop and remove services
./logs.sh             # Tail logs
./status.sh           # Show container status
./build-package.sh    # Build deployment package (.tar.gz)
```

---

## Development (Local)

- Backend (hot reload):

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Frontend (dev server):

```bash
cd frontend
npm install
npm start
```

- Ensure your `.env` is present and MongoDB is reachable (run via Docker or local Mongo).

---

## Sample Data

- `sample_data_conditions.csv`, `test_ehr_data.csv`
- `test_data/sample_fhir_resources.json` (JSON examples)
- Minimal OMOP vocab subset seeded into SQLite (subset files mounted via volume)

---

## Troubleshooting

- Gemini errors: `API key not valid`
  - Set `GEMINI_API_KEY` in `.env`, restart containers
  - Verify inside container: `docker-compose exec app env | grep GEMINI_API_KEY`

- UI “Loading…” on ingestion jobs
  - Ensure backend reachable at `http://localhost:8000`
  - Check browser console/network; see enhanced logging in `frontend/src/App.jsx`

- 0 records persisted to OMOP
  - Confirm appropriate ingestion job selected
  - Verify FHIR resources exist for `jobId` in `fhir_*` collections

- Frontend build warnings (eslint)
  - Warnings are expected in production build; not blocking

---

## Security & Compliance (Dev Notes)

- This repository is a PoC/Dev tool; not production hardened
- Secrets should be stored securely in production (Vault/Secret Manager)
- PHI/PII: do not use real patient data outside compliant environments

---

## License

Add your organization’s license here (e.g., Apache-2.0 / MIT).

---

## Acknowledgements

- HL7® FHIR® specifications
- OHDSI OMOP Common Data Model
- Google Gemini, Sentence‑BERT (Bio/Clinical embeddings)

---

## Getting Help

- Restart: `./stop.sh && ./start.sh`
- Logs: `./logs.sh` or `docker-compose logs -f`
- Key guide: `GEMINI_API_KEY_UPDATE.md`

Happy building! 🚀
