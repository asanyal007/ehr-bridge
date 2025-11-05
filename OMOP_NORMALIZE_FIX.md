# Fix: OMOP "Normalize Concepts" Button

## Problem

The "Normalize Concepts" button in the OMOP Data Model tab was not working because:

1. **Missing Context**: The function was looking for `currentJob.finalMappings` which doesn't exist in the OMOP workflow
2. **No Data Source**: It wasn't fetching actual data from ingested records
3. **Hard-coded Values**: It was using synthetic sample values instead of real data

## Solution

Enhanced the `generateOmopConcepts()` function in `frontend/src/App.jsx` to:

### 1. Use OMOP Table Prediction
```javascript
const targetTable = omopPrediction?.table || 'PERSON';
```
- Uses the predicted OMOP table to determine which concepts to normalize
- Falls back to PERSON if no prediction exists

### 2. Fetch Real Ingested Data
```javascript
const ingestResp = await axios.get(
  `${API_BASE_URL}/api/v1/ingestion/records/${currentJob.jobId}?limit=10`,
  { headers: { ...authHeaders } }
);
sampleRecords = ingestResp.data.records || [];
```
- Fetches up to 10 actual records from the ingestion job
- Gracefully handles cases where no records exist yet

### 3. Smart Field Mapping
```javascript
const domainFields = {};
if (targetTable === 'CONDITION_OCCURRENCE') {
  domainFields['condition_concept_id'] = {
    domain: 'Condition',
    sourceFields: ['primary_diagnosis_icd10', 'diagnosis_code', 'icd10', 'icd_code']
  };
}
// ... similar for MEASUREMENT and DRUG_EXPOSURE
```
- Maps OMOP tables to their concept ID fields
- Defines source field patterns to look for in the data

### 4. Extract Real Values
```javascript
for (const record of sampleRecords) {
  for (const sourceField of config.sourceFields) {
    const val = record[sourceField];
    if (val && !sampleValues.includes(val)) {
      sampleValues.push(val);
    }
  }
}
```
- Extracts unique values from actual data
- Falls back to synthetic examples if no data exists

### 5. Better Error Handling
```javascript
alert(`Generated ${Object.keys(suggestions).length} concept normalization suggestion(s) for ${targetTable}`);
```
- Provides user feedback on success
- Shows detailed error messages on failure

## Testing Instructions

### Prerequisites
1. Backend server running on port 8000
2. Frontend running on port 3000
3. At least one ingestion job with data

### Test Steps

1. **Navigate to an Ingestion Job:**
   - Go to "Mapping + Ingestion" view
   - Find a job with status "APPROVED" or that has ingested data
   - Click "Data Model" in the actions menu

2. **Predict OMOP Table:**
   - Switch to "OMOP" tab
   - Click "Predict OMOP Table" button
   - Verify that a table is predicted (e.g., CONDITION_OCCURRENCE, MEASUREMENT)

3. **Test Normalize Concepts:**
   - Click "Normalize Concepts" button
   - Wait for the alert message (should say "Generated X concept normalization suggestion(s)")
   - Verify that a "Concept Normalization" section appears below

4. **Verify Normalization Results:**
   - Check that real values from your data appear (not just synthetic values)
   - Verify concept_id mappings are shown
   - Check confidence levels (High/Medium/Low badges)
   - Try editing a concept_id value

5. **Test with Different OMOP Tables:**
   - Test with CONDITION_OCCURRENCE (ICD-10 codes)
   - Test with MEASUREMENT (LOINC codes)
   - Test with DRUG_EXPOSURE (RxNorm/drug names)

### Expected Results

✅ **Success Indicators:**
- Alert shows "Generated 1 concept normalization suggestion(s) for [TABLE_NAME]"
- Concept Normalization section appears with a purple/blue background
- Real values from your data are shown (e.g., actual ICD-10 codes like C50.9, E11.9)
- Each value shows:
  - Source value (e.g., C50.9)
  - Arrow separator (→)
  - Concept ID input field (editable)
  - Concept name (e.g., "Malignant neoplasm of breast")
  - Confidence badge (High/Medium/Low)

❌ **Failure Scenarios Handled:**
- If no ingested data: Uses fallback synthetic values
- If prediction fails: Defaults to PERSON table (may not generate concepts)
- If API error: Shows detailed error message in alert

## Backend Endpoints Used

1. **GET `/api/v1/ingestion/records/{job_id}?limit=10`**
   - Fetches sample records for value extraction
   
2. **POST `/api/v1/omop/concepts/normalize`**
   - Request: `{ values: [...], domain: "Condition|Measurement|Drug" }`
   - Response: `{ success: true, suggestions: [...], count: N }`

## Example Workflow

```
User clicks "Normalize Concepts"
  ↓
Fetch 10 sample records from ingestion job
  ↓
Extract unique values for diagnosis codes (e.g., C50.9, E11.9, I10)
  ↓
Call /api/v1/omop/concepts/normalize with domain="Condition"
  ↓
Display normalized concepts with confidence scores
  ↓
User can edit concept_id values
  ↓
User clicks "Save Mappings" to persist
```

## Related Files

- **Frontend**: `frontend/src/App.jsx` (lines 457-543)
- **Backend API**: `backend/main.py` (line 998)
- **Vocabulary Service**: `backend/omop_vocab.py`

## Future Enhancements

1. Support for VISIT_OCCURRENCE and OBSERVATION tables
2. Batch processing for large datasets
3. Vocabulary search/browse UI
4. Custom concept mapping overrides
5. Export/import concept mappings
6. Concept relationship visualization

## Notes

- The fix is backward compatible - existing functionality unchanged
- No database migrations required
- Works with both real data and synthetic fallbacks
- Gracefully handles missing or incomplete data

