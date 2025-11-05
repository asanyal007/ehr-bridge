# OMOP Integration Enhancements

## Overview
This document summarizes the enhancements made to close gaps in the OMOP CDM integration for the EHR Data Interoperability Platform.

## Implemented Features

### 1. Top-3 OMOP Table Predictions with Confidence Scoring
**File**: `backend/omop_engine.py`

- **Enhanced Heuristics**: Improved scoring algorithm that evaluates schema fields against OMOP table characteristics
- **Confidence Calculation**: Normalized confidence scores (0.6-0.95 range) based on relative scoring
- **Top-3 Alternatives**: Always returns the top 3 predicted tables with their individual confidence scores and rationales
- **Threshold Gating**: Automatically flags low-confidence predictions (< 0.7) for manual review

**Example Response**:
```json
{
  "table": "CONDITION_OCCURRENCE",
  "confidence": 0.89,
  "rationale": "Heuristic match based on 7 matching schema fields",
  "alternatives": [
    {
      "table": "CONDITION_OCCURRENCE",
      "confidence": 0.89,
      "rationale": "Heuristic match based on 7 matching schema fields",
      "score": 7
    },
    {
      "table": "PERSON",
      "confidence": 0.60,
      "rationale": "Heuristic match based on 0 matching schema fields",
      "score": 0
    },
    {
      "table": "VISIT_OCCURRENCE",
      "confidence": 0.60,
      "rationale": "Heuristic match based on 0 matching schema fields",
      "score": 0
    }
  ]
}
```

### 2. PersonIDService and VisitIDService Integration
**Files**: `backend/omop_engine.py`, `backend/person_id_service.py`, `backend/visit_id_service.py`

- **Stable ID Generation**: Deterministic `person_id` generation using demographic keys (MRN, first name, last name, DOB)
- **Caching Layer**: SQLite-backed cache for previously generated IDs to ensure consistency across runs
- **Key Normalization**: Case-insensitive, whitespace-trimmed key handling
- **Last Seen Tracking**: Timestamps for audit trail

**Integration Points**:
- `_extract_person()`: Uses PersonIDService for CSV-like row extraction
- `persist_all_omop()`: Uses PersonIDService for FHIR Patient transformation
- FHIR MRN extraction from identifiers with system="MRN"

### 3. CSV-Based OMOP Vocabulary Seeding
**File**: `backend/omop_vocab.py`

Added two new methods to `OMOPVocabService`:

#### `load_concepts_from_csv(csv_path: str) -> int`
Loads concepts from a single CSV file with expected columns:
- `concept_id`, `concept_name`, `domain_id`, `vocabulary_id`
- `concept_code`, `standard_concept`, `concept_class_id`
- `valid_start_date`, `valid_end_date`

#### `seed_from_directory(vocab_dir: str) -> Dict[str, int]`
Bulk loader that processes all CSV files in a directory:
- Default directory: `data/omop_vocab_seed/`
- File naming convention: `{Vocabulary}.csv` (e.g., `ICD10CM.csv`, `LOINC.csv`)
- Returns dictionary of loaded counts per vocabulary
- Gracefully handles malformed rows with warnings

**Sample CSV Format**:
```csv
concept_id,concept_name,domain_id,vocabulary_id,concept_code,standard_concept,concept_class_id,valid_start_date,valid_end_date
900101,Malignant neoplasm of prostate,Condition,ICD10CM,C61,S,Diagnosis,2020-01-01,2099-12-31
910101,Creatinine [Mass/volume] in Serum or Plasma,Measurement,LOINC,2160-0,S,Lab Test,2020-01-01,2099-12-31
```

**Usage Example**:
```python
from omop_vocab import get_vocab_service

vs = get_vocab_service()
results = vs.seed_from_directory('../data/omop_vocab_seed')
# Returns: {'ICD10CM_sample': 5, 'LOINC_sample': 4}
```

### 4. OMOP Statistics Endpoint
**File**: `backend/main.py`

New endpoint: `GET /api/v1/omop/stats`

**Features**:
- Real-time collection counts for all OMOP tables
- Total record count across all tables
- Auto-discovery of OMOP collections (prefixed with `omop_`)
- MongoDB configuration detection from ingestion engine

**Response Format**:
```json
{
  "success": true,
  "total_records": 12,
  "tables": {
    "PERSON": 12
  },
  "table_count": 1
}
```

**Use Cases**:
- Dashboard statistics display
- Data validation and coverage reporting
- ETL pipeline monitoring
- Quality assurance checks

## Testing

### Table Prediction
```bash
curl -X POST http://localhost:8000/api/v1/omop/predict-table \
  -H "Content-Type: application/json" \
  -d '{"primary_diagnosis_icd10": "string", "diagnosis_date": "string"}'
```

### OMOP Stats
```bash
curl http://localhost:8000/api/v1/omop/stats
```

### Vocabulary Seeding
```python
from omop_vocab import get_vocab_service
vs = get_vocab_service()
results = vs.seed_from_directory('../data/omop_vocab_seed')
print(f"Loaded: {results}")
```

## Benefits

1. **Improved Accuracy**: Top-3 predictions give users options when schema is ambiguous
2. **Data Integrity**: PersonIDService ensures consistent patient identification across tables
3. **Scalability**: CSV seeding allows easy expansion of vocabulary coverage
4. **Observability**: Stats endpoint enables real-time monitoring and validation
5. **Auditability**: ID services maintain creation and last-seen timestamps

## Next Steps

1. Add VisitIDService usage in VISIT_OCCURRENCE transformations
2. Implement Gemini-backed table prediction as alternative to heuristics
3. Add confidence threshold configuration (environment variable)
4. Expand vocabulary seeding to include concept relationships
5. Add vocabulary stats to the `/omop/stats` endpoint
6. Implement vocabulary search UI component
7. Add batch concept normalization endpoint for large datasets

## Architecture Notes

- All services use singleton pattern for efficient resource usage
- SQLite databases are auto-created on first access
- MongoDB connections reuse existing ingestion engine configuration
- Error handling is graceful with appropriate fallbacks
- All endpoints maintain backward compatibility

