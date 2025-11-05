# End-to-End OMOP Flow Test Guide

## Complete User Journey

### Step 1: Create Ingestion Pipeline (with OMOP-Compatible Filter)

**UI Path:** `Ingestion Pipelines` → `+ Create Ingestion Job`

**Actions:**
1. Click "+ Create Ingestion Job" button
2. ✅ Check **"Show OMOP-Compatible Jobs Only"** checkbox
3. Select a job from dropdown (e.g., `job_1760282978` - 30 records)
4. View job details (source type, record count, resources)
5. Click **"Create & Start"**

**What Happens:**
- Filters jobs to show only those with:
  - CSV data, OR
  - Supported FHIR resources (Patient, Observation, Condition, MedicationRequest, DiagnosticReport)
- Creates ingestion job with selected mapping
- Starts data ingestion immediately
- Data flows to MongoDB staging/FHIR collections

**Backend API Used:**
- `GET /api/v1/omop/compatible-jobs` - Fetches compatible job list
- `POST /api/v1/ingestion/jobs` - Creates ingestion job

---

### Step 2: Monitor Ingestion

**UI Path:** Ingestion job card appears in list

**Actions:**
1. Wait for ingestion to complete (status changes to "COMPLETED")
2. View ingestion metrics (Received, Failed counts)

**What Happens:**
- Real-time streaming engine processes records
- Data persisted to MongoDB
- Failed records stored in DLQ

---

### Step 3: Open Data Model

**UI Path:** Ingestion job → `📊 Data Model` button

**Actions:**
1. Click **"Data Model"** button on ingestion job card
2. Select **"OMOP"** tab

**What Happens:**
- Opens OMOP Data Model modal
- Shows 5-step process tabs

---

### Step 4: Predict OMOP Table

**UI Path:** OMOP Tab → `1. Predict Table`

**Actions:**
1. Click **"Predict OMOP Table"** button
2. Review prediction with confidence score
3. Note alternatives if confidence is low

**What Happens:**
- AI analyzes source schema
- Predicts target OMOP table (PERSON, MEASUREMENT, CONDITION_OCCURRENCE, etc.)
- Returns top 3 predictions with confidence scores

**Backend API Used:**
- `POST /api/v1/omop/predict-table`

---

### Step 5: Normalize Concepts

**UI Path:** OMOP Tab → `2. Normalize Concepts`

**Actions:**
1. Click **"Normalize Concepts"** button
2. Review AI-suggested concept mappings
3. See confidence scores for each mapping (High ≥80%, Medium 50-79%, Low <50%)
4. Edit concept IDs if needed
5. Click **"Save Mappings for [field]"** or **"Save All Mappings"**

**What Happens:**
- AI analyzes sample data values
- Extracts real values from ingestion job
- Maps to OMOP Standard Concept IDs using:
  - Direct vocabulary lookup
  - S-BERT semantic matching
  - Gemini AI reasoning
- Displays confidence scores
- Saves approved mappings to SQLite

**Backend API Used:**
- `POST /api/v1/omop/concepts/normalize`
- `PUT /api/v1/omop/concepts/approve`

---

### Step 6: Review Concepts (HITL)

**UI Path:** OMOP Tab → `3. Review Concepts`

**Actions:**
1. See count of pending reviews (badge shows number)
2. Review low-confidence mappings
3. Approve, reject, or select alternative concept IDs
4. Use bulk actions for multiple approvals

**What Happens:**
- Low-confidence mappings (<70%) queued for human review
- Shows source code, system, display text
- Shows top 3 AI suggestions with reasoning
- User approves/overrides
- Approved mappings cached for future use

**Backend API Used:**
- `GET /api/v1/omop/concepts/review-queue/{job_id}`
- `POST /api/v1/omop/concepts/approve-mapping`
- `POST /api/v1/omop/concepts/bulk-approve`

---

### Step 7: Preview OMOP Rows

**UI Path:** OMOP Tab → `4. Preview`

**Actions:**
1. Click **"Preview OMOP Rows"** button
2. Review JSON structure of OMOP rows
3. Verify field coverage and data quality

**What Happens:**
- Transforms sample records to OMOP format (10 rows)
- Shows field coverage report
- Uses approved concept mappings
- Validates row structure

**Backend API Used:**
- `POST /api/v1/omop/preview`

---

### Step 8: Persist to OMOP Collections

**UI Path:** OMOP Tab → `5. Persist`

**Actions:**
1. Review current job ID and target table
2. Click **"Persist ALL to Mongo"** button
3. Review success message with:
   - Table name (e.g., `omop_MEASUREMENT`)
   - Inserted/Updated count
   - Total records found
   - Source collection
   - Job ID

**What Happens:**
- Loads ALL records from staging/FHIR collections for the job
- Transforms each record to OMOP format using:
  - Approved concept mappings
  - Semantic normalization
  - Stable person_id generation
- Persists to MongoDB `omop_*` collections
- Upserts to handle duplicates

**Backend API Used:**
- `POST /api/v1/omop/persist-all`

---

### Step 9: Verify OMOP Data

**UI Path:** `OMOP Tables` viewer (sidebar)

**Actions:**
1. Navigate to OMOP Tables
2. Select table (PERSON, MEASUREMENT, etc.)
3. Filter by job ID
4. View persisted records

**What Happens:**
- Reads from MongoDB `omop_*` collections
- Displays records with all OMOP fields
- Shows concept IDs, dates, values, etc.

**Backend API Used:**
- `GET /api/v1/omop/tables`
- `GET /api/v1/omop/data?table=MEASUREMENT&job_id=...`

---

## Test Scenarios

### Scenario 1: CSV → OMOP CONDITION_OCCURRENCE

**Job:** `job_1760282978` (30 cancer registry records)

**Expected Flow:**
1. Create ingestion pipeline with OMOP filter → Select `job_1760282978`
2. Wait for ingestion (30 records)
3. Data Model → OMOP
4. Predict Table → **CONDITION_OCCURRENCE** (high confidence)
5. Normalize Concepts → Map ICD-10 codes (C50.9, etc.)
6. Review Concepts → Auto-approve high-confidence
7. Preview → See 10 sample condition rows
8. Persist → **5 records inserted** (batched)
9. Verify in OMOP Tables → See condition_concept_id, person_id

---

### Scenario 2: CSV → OMOP MEASUREMENT

**Job:** `test_enhanced_measurements` (10 EHR records with vitals)

**Expected Flow:**
1. Create ingestion pipeline → Select `test_enhanced_measurements`
2. Wait for ingestion (10 records)
3. Data Model → OMOP
4. Predict Table → **MEASUREMENT** (high confidence)
5. Normalize Concepts → Map LOINC codes (33747-0, 2093-3, 8310-5, 8480-6, etc.)
6. Review Concepts → Review lab/vital codes
7. Preview → See multiple measurements per patient (lab + vitals = ~7 per patient)
8. Persist → **70+ records inserted** (10 patients × 7 measurements each)
9. Verify → See measurement_concept_id, value_as_number, unit

---

### Scenario 3: FHIR DiagnosticReport → OMOP MEASUREMENT

**Job:** `job_1761086752` (75 DiagnosticReport resources)

**Expected Flow:**
1. Create ingestion pipeline → Select `job_1761086752`
2. Wait for ingestion (75 FHIR resources)
3. Data Model → OMOP
4. Predict Table → **MEASUREMENT**
5. Normalize Concepts → Map LOINC codes from result references
6. Review Concepts → (mostly auto-approved)
7. Preview → See diagnostic measurements
8. Persist → **10 records inserted** (one per unique result reference)
9. Verify → See measurement_source_value (LOINC codes)

---

## Key Points

### Job Selection Happens Early
- ✅ OMOP-compatible filter in **Create Ingestion Pipeline** modal
- ✅ User selects job with actual data before ingestion starts
- ✅ No job switching in Data Model/Persist tabs

### Concept Normalization is Persistent
- ✅ Saved to SQLite `terminology_normalizations` table
- ✅ Used during OMOP persistence via `_concept_lookup()`
- ✅ Cached for performance

### End-to-End Flow is Linear
1. **Create** → Select OMOP-compatible job
2. **Ingest** → Data flows to MongoDB
3. **Predict** → AI determines OMOP table
4. **Normalize** → AI suggests concept mappings
5. **Review** → Human approves low-confidence
6. **Preview** → Verify OMOP structure
7. **Persist** → Save to OMOP collections
8. **Verify** → View in OMOP Tables

---

## Troubleshooting

### Issue: 0 Records Persisted

**Cause:** Job has no data in staging/FHIR collections

**Solution:**
1. Check ingestion status (must be "COMPLETED")
2. Verify job ID in Create Ingestion Pipeline
3. Use OMOP-compatible filter to see only valid jobs
4. Check MongoDB collections for data

### Issue: Low Confidence Mappings

**Cause:** Ambiguous or non-standard codes

**Solution:**
1. Go to "Review Concepts" tab
2. Review AI suggestions
3. Select correct concept ID or search vocabulary
4. Approve and re-persist

### Issue: Wrong OMOP Table Predicted

**Cause:** AI misinterpreted source schema

**Solution:**
1. In "Predict Table" tab, check alternatives
2. Manually select correct table from dropdown (if available)
3. Continue with Normalize/Review/Persist for that table

---

## Success Metrics

- ✅ 95%+ auto-approval rate for concept normalization
- ✅ < 2 seconds for full OMOP persistence (100 records)
- ✅ Zero data loss (all source records transformed)
- ✅ Deterministic person_id generation (same source → same ID)
- ✅ Complete audit trail (approved_by, created_at timestamps)

