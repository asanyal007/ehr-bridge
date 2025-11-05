# Ingestion Job Testing Guide

## ✅ What Was Fixed

### 1. Data Model Modal Job ID Fix
- **Before:** Modal used mapping job ID → No data found
- **After:** Modal uses ingestion job ID → Data found and persisted ✅

### 2. Enhanced Failed Records Display
- **Before:** Raw JSON dump
- **After:** Structured display with:
  - Clear error messages
  - Source data separation
  - Contextual fix suggestions
  - Timestamp and record numbers

## 🧪 How to Test

### Test 1: View Failed Records

**Steps:**
1. Go to "Ingestion Pipelines" screen
2. Find the ingestion job: `UI_Ingestion_Pipeline` (`job_1761090484`)
3. Click "⚠ View Failed" button

**Expected Result:**
```
❌ 4 record(s) failed to ingest

┌────────────────────────────────┐
│ Record #1                      │
│ Error: simulated_failure       │
│ 10/21/2025, 11:48:09 PM       │
├────────────────────────────────┤
│ Source Data:                   │
│ {                              │
│   "patient_id": "P001",       │
│   "first_name": "John",       │
│   "diagnosis_code": "E11.9"   │
│   ...                          │
│ }                              │
├────────────────────────────────┤
│ 💡 Tip: This is a simulated   │
│ failure for testing. Remove    │
│ test failures in production.   │
└────────────────────────────────┘
```

**What to Check:**
- ✅ 4 failed records displayed
- ✅ Each shows error reason clearly
- ✅ Source data is formatted and readable
- ✅ Contextual tips are shown
- ✅ Timestamps are displayed

---

### Test 2: OMOP Persistence with Working Jobs

**Steps:**
1. Go to "Ingestion Pipelines" screen
2. Find an ingestion job with actual data (not just metrics)
3. Click "📊 Data Model" button
4. Select "OMOP" tab
5. Note the Job ID in the modal title
6. Click through: Predict → Normalize → Review → Preview → Persist

**Working Test Jobs:**
| Job ID | Records | Data Location | Expected OMOP Table |
|--------|---------|---------------|---------------------|
| `job_1760323358` | 305 | staging | CONDITION_OCCURRENCE |
| `job_1760282978` | 30 | staging | CONDITION_OCCURRENCE |
| `sample_job_001` | 11 | fhir_* | PERSON |

**Expected Result for `job_1760323358`:**
```
✅ OMOP Persist Complete

Table: omop_CONDITION_OCCURRENCE
Inserted/Updated: 10 rows
Total Records Found: 305
Source: staging collection (job_id=job_1760323358)
Job ID: job_1760323358...
```

**What to Check:**
- ✅ Job ID in modal matches ingestion job ID (not mapping job ID)
- ✅ "Total Records Found" > 0
- ✅ "Inserted/Updated" > 0
- ✅ No error about "0 records found"
- ✅ Data appears in OMOP Tables viewer

---

### Test 3: Create New Ingestion Job with OMOP Filter

**Steps:**
1. Go to "Ingestion Pipelines" screen
2. Click "+ Create Ingestion Job"
3. Check "Show OMOP-Compatible Jobs Only"
4. Observe dropdown changes to show only compatible jobs
5. Select a job (e.g., `job_1760323358`)
6. Note the job details panel shows:
   - Type: csv
   - Records: 305
   - Resources: staging
7. Click "Create & Start"
8. Wait for ingestion to complete
9. Click "📊 Data Model"
10. Verify modal uses the correct job ID

**Expected Result:**
- ✅ Dropdown filters to show only jobs with actual data
- ✅ Job details panel shows accurate info
- ✅ Data Model opens with correct ingestion job ID
- ✅ OMOP persistence finds and processes records

---

### Test 4: Malformed Data Handling

**Job:** `job_1761090484` (94 records, but malformed FHIR)

**Steps:**
1. Click "📊 Data Model" on this job
2. Try to persist to OMOP
3. Observe result

**Expected Result:**
```
⚠️ OMOP Persist Complete

Table: omop_PERSON
Inserted/Updated: 0 rows
Total Records Found: 0
Source: Unknown
Job ID: job_1761090484...
```

**Why 0 records?**
- Data exists in staging (94 records)
- BUT records are malformed FHIR (Patient resources with invalid fields)
- OMOP transformer can't process malformed data
- This is expected behavior - garbage in, garbage out

**What to Check:**
- ✅ No crash or exception
- ✅ Clear message about 0 records found
- ✅ User can investigate by checking "View Records"
- ✅ Failed records (if any) are in DLQ

---

## 📊 Database Verification Commands

### Check Job Data:
```bash
cd /Users/aritrasanyal/EHR_Test/backend && python3 << 'EOF'
from mongodb_client import get_mongo_client

client = get_mongo_client().client
db = client['ehr']

job_id = 'job_1761090484'  # Change this to your test job ID

print(f'Checking data for: {job_id}')
print('=' * 60)

for coll_name in db.list_collection_names():
    if coll_name.startswith('system.'):
        continue
    count = db[coll_name].count_documents({'job_id': job_id})
    if count > 0:
        print(f'{coll_name}: {count} records')
        
        # Show sample
        sample = db[coll_name].find_one({'job_id': job_id})
        if sample:
            resource_type = sample.get('resourceType', 'CSV/Raw')
            print(f'  Type: {resource_type}')
            print(f'  Keys: {list(sample.keys())[:10]}')
            print()
EOF
```

### Test OMOP API Directly:
```bash
curl -X POST http://localhost:8000/api/v1/omop/persist-all \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token-123" \
  -d '{"job_id": "job_1760323358", "table": null}' | json_pp
```

### List OMOP-Compatible Jobs:
```bash
curl -X GET http://localhost:8000/api/v1/omop/compatible-jobs \
  -H "Authorization: Bearer test-token-123" | json_pp
```

Expected output:
```json
{
  "compatible_jobs": [
    {
      "job_id": "job_1760323358",
      "source_type": "csv",
      "record_count": 305,
      "resource_types": ["staging"],
      "omop_ready": true
    },
    ...
  ]
}
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "0 records found" when data exists

**Symptom:** 
- Ingestion job shows 94 processed records
- OMOP persist says "0 records found"

**Causes:**
1. Wrong job ID (mapping ID instead of ingestion ID) → **FIXED ✅**
2. Malformed FHIR resources → Check data quality
3. Data in wrong collection → Check MongoDB

**Solution:**
- Use the OMOP-compatible filter when creating ingestion jobs
- Verify data structure with database commands above
- Check failed records for transformation errors

### Issue 2: Failed records not showing

**Symptom:**
- Ingestion shows "4 failed"
- "View Failed" shows "No failed records"

**Cause:** DLQ collection not created or wrong job ID

**Solution:**
```bash
cd /Users/aritrasanyal/EHR_Test/backend && python3 << 'EOF'
from mongodb_client import get_mongo_client

client = get_mongo_client().client
db = client['ehr']

# Check DLQ
dlq_count = db['staging_dlq'].count_documents({})
print(f'Total failed records in DLQ: {dlq_count}')

# Group by job_id
pipeline = [
    {'$group': {'_id': '$job_id', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]
results = list(db['staging_dlq'].aggregate(pipeline))
for r in results:
    print(f"  {r['_id']}: {r['count']} failed records")
EOF
```

### Issue 3: Simulated failures in production

**Symptom:** 1 out of 20 records always fails with "simulated_failure"

**Cause:** Test mode enabled in ingestion engine

**Solution:** 
Edit `backend/ingestion_engine.py` lines 316-322:
```python
# Remove this block for production:
if self.metrics.received % 20 == 0:
    self.metrics.failed += 1
    failed_sample = self._rows[(self._row_idx) % len(self._rows)]
    self._write_failed_to_mongo(failed_sample, reason="simulated_failure")
```

---

## ✅ Success Criteria

**A successful ingestion flow should:**

1. **Create Ingestion Job:**
   - ✅ OMOP-compatible filter shows only valid jobs
   - ✅ Job details panel shows accurate data
   - ✅ Selected job has actual records in MongoDB

2. **Run Ingestion:**
   - ✅ Metrics update in real-time (Received, Processed, Failed)
   - ✅ Successful records written to staging/FHIR collections
   - ✅ Failed records written to DLQ with error reasons

3. **View Records:**
   - ✅ "View Records" shows successfully ingested data
   - ✅ "View Failed" shows detailed error breakdown
   - ✅ Error messages are clear and actionable

4. **Data Model & OMOP:**
   - ✅ "Data Model" opens with correct ingestion job ID
   - ✅ OMOP prediction finds appropriate table
   - ✅ Concept normalization works
   - ✅ Preview shows transformed OMOP rows
   - ✅ Persist writes data to OMOP collections

5. **Verify Results:**
   - ✅ OMOP Tables viewer shows persisted data
   - ✅ Record counts match expectations
   - ✅ Data quality is maintained

---

## 📝 Key Takeaways

1. **Always use ingestion job IDs for data operations** (not mapping job IDs)
2. **Check data quality before ingestion** (avoid malformed FHIR)
3. **Monitor failed records** via the enhanced DLQ viewer
4. **Use OMOP-compatible filter** to avoid selecting empty jobs
5. **Verify data at each step** (ingestion → staging → OMOP)

---

## 🔄 Complete End-to-End Flow

```
1. Create Mapping Job (CSV → FHIR)
   └─ Defines source schema, target FHIR resource, field mappings

2. Create Ingestion Job (from Mapping Job)
   ├─ Uses OMOP-compatible filter
   ├─ Selects job with actual data (e.g., job_1760323358)
   └─ Creates streaming pipeline

3. Start Ingestion
   ├─ Receives CSV records
   ├─ Transforms using mapping rules
   ├─ Writes FHIR to staging/fhir_* collections
   └─ Writes failures to DLQ

4. Monitor Ingestion
   ├─ View real-time metrics (Received, Processed, Failed)
   ├─ Check "View Records" for successful data
   └─ Check "View Failed" for errors

5. Open Data Model (OMOP Tab)
   ├─ Modal uses INGESTION job ID ✅
   ├─ Predict OMOP table (e.g., CONDITION_OCCURRENCE)
   ├─ Normalize concepts (map codes to OMOP IDs)
   ├─ Review low-confidence mappings (HITL)
   ├─ Preview OMOP rows
   └─ Persist to omop_* collections

6. Verify OMOP Data
   ├─ Go to "OMOP Tables" viewer
   ├─ Select table and filter by job ID
   └─ See transformed OMOP records
```

---

## 🎯 Next Steps

1. **Remove Test Failures:** Update ingestion engine to disable simulated failures
2. **Fix FHIR Transformation:** Ensure CSV → FHIR produces valid resources
3. **Add Data Validation:** Validate FHIR resources before persistence
4. **Implement Retry:** Allow users to retry failed records from UI
5. **Add Export:** Export failed records as CSV for offline analysis
6. **Real-time Updates:** WebSocket support for live metrics

---

**Last Updated:** October 22, 2025  
**Status:** ✅ Ingestion job error handling and OMOP persistence fixed

