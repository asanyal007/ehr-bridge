# Ingestion and Chatbot Implementation Fixes

**Date**: 2024-12-19  
**Session Summary**: Fixed ingestion job data persistence, improved error visibility, integrated LM Studio for FHIR chatbot, and implemented agentic query processing.

---

## Table of Contents

1. [Ingestion Job Fixes](#ingestion-job-fixes)
2. [Error Visibility Improvements](#error-visibility-improvements)
3. [FHIR Chatbot LM Studio Integration](#fhir-chatbot-lm-studio-integration)
4. [Agentic Chatbot Enhancements](#agentic-chatbot-enhancements)
5. [Path Resolution Fixes](#path-resolution-fixes)

---

## Ingestion Job Fixes

### Problem
Ingestion jobs were showing records as "Processed" in the UI, but no records were actually being written to MongoDB. The `processed` counter was being incremented regardless of whether the write operation succeeded.

### Root Cause
1. **False Positive Metrics**: The `processed` counter was incremented before verifying that the MongoDB write actually succeeded
2. **Silent Failures**: `_write_to_mongo()` was swallowing all exceptions without logging
3. **Missing Validation**: Jobs could start even when source data or destination wasn't properly configured

### Solution

#### 1. Fixed `_write_to_mongo()` Method
**File**: `backend/ingestion_engine.py`

**Changes**:
- Changed return type to `bool` to indicate success/failure
- Added proper error logging instead of silently swallowing exceptions
- Returns `True` on success, `False` on failure

```python
def _write_to_mongo(self, record: Dict[str, Any]) -> bool:
    """
    Write record to MongoDB destination
    
    Returns:
        True if successful, False otherwise
    """
    if not self._mongo_client:
        print(f"[WARN] Ingestion job {self.config.job_id}: MongoDB client not initialized")
        return False
    try:
        db_name = self.config.destination_connector.config.get('database', 'ehr')
        coll_name = self.config.destination_connector.config.get('collection', 'staging')
        db = self._mongo_client[db_name]
        coll = db[coll_name]
        doc = dict(record)
        doc['job_id'] = self.config.job_id
        doc['ingested_at'] = datetime.utcnow()
        coll.insert_one(doc)
        return True
    except Exception as e:
        print(f"[ERROR] Ingestion job {self.config.job_id}: Failed to write to MongoDB: {e}")
        return False
```

#### 2. Fixed Processing Loop
**File**: `backend/ingestion_engine.py` - `_run_loop()` method

**Changes**:
- Only increment `processed` if `_write_to_mongo()` returns `True`
- If write fails, increment `failed` and send to DLQ
- Added early exit if source data or destination not available
- Better error handling with proper logging

```python
if out_doc is not None:
    write_success = self._write_to_mongo(out_doc)
    if write_success:
        # Only increment processed if write was successful
        self.metrics.processed += 1
    else:
        # Write failed, count as failed
        self.metrics.failed += 1
        self._write_failed_to_mongo(record, reason="mongodb_write_failed")
```

#### 3. Added Pre-Start Validation
**File**: `backend/ingestion_engine.py` - `start()` method

**Changes**:
- Validates source data availability before starting
- Validates destination configuration before starting
- Sets status to "ERROR" if validation fails
- Returns `False` if validation fails, preventing job from starting

```python
# Validate configuration before starting
has_source = bool(self._rows) if self.config.source_connector.connector_type == ConnectorType.csv_file else True
has_destination = bool(self._mongo_client) if self.config.destination_connector.connector_type == ConnectorType.mongodb else True

if not has_source:
    error_msg = f"Cannot start - no source data available..."
    self.status = "ERROR"
    self.error_message = error_msg
    return False
```

---

## Error Visibility Improvements

### Problem
When ingestion jobs failed with status "ERROR", users couldn't see what the actual error was. The UI only showed "ERROR" status with no details.

### Solution

#### 1. Added Error Tracking to IngestionJob
**File**: `backend/ingestion_engine.py`

**Added Fields**:
```python
self.error_message: Optional[str] = None
self.error_details: Optional[Dict[str, Any]] = None
```

**Error Types Tracked**:
- `source_missing`: No source data available
- `destination_missing`: MongoDB destination not configured
- `runtime_error`: Fatal error during processing

#### 2. Enhanced Job Status Response
**File**: `backend/ingestion_engine.py` - `_job_status_dict()` method

**Changes**:
- Includes error information when status is "ERROR"
- Provides both human-readable message and technical details

```python
if job.status == "ERROR":
    status_dict["error"] = {
        "message": job.error_message or "Unknown error occurred",
        "details": job.error_details or {}
    }
```

#### 3. Frontend Error Display
**File**: `frontend/src/App.jsx`

**Changes**:
- Added red error box when status is "ERROR"
- Displays error message prominently
- Includes expandable "technical details" section
- Changed ERROR status color to red (was amber)

```jsx
{j.status === 'ERROR' && j.error && (
  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
    <p className="text-sm font-semibold text-red-800 mb-1">Error Details:</p>
    <p className="text-sm text-red-700">{j.error.message || j.error || 'Unknown error occurred'}</p>
    {j.error.details && Object.keys(j.error.details).length > 0 && (
      <details className="mt-2">
        <summary className="text-xs text-red-600 cursor-pointer hover:text-red-800">Show technical details</summary>
        <pre className="mt-2 text-xs text-red-600 bg-red-100 p-2 rounded overflow-auto max-h-40">
          {JSON.stringify(j.error.details, null, 2)}
        </pre>
      </details>
    )}
  </div>
)}
```

---

## FHIR Chatbot LM Studio Integration

### Problem
The FHIR chatbot was using Google Gemini API, but the user wanted to use LM Studio running locally.

### Solution

#### 1. Replaced Gemini with LM Studio HTTP API
**File**: `backend/fhir_chatbot_service.py`

**Removed**:
- `google.generativeai` import and configuration
- Gemini API key dependency

**Added**:
- `requests` library for HTTP calls
- `_call_lm_studio()` method for API calls

#### 2. LM Studio Configuration
**File**: `backend/fhir_chatbot_service.py`

**Configuration**:
- Base URL: `http://127.0.0.1:1234` (configurable via `LM_STUDIO_URL` env var)
- Endpoint: `/v1/chat/completions`
- Model: `"local-model"` (LM Studio default)

**Implementation**:
```python
def _call_lm_studio(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 2000) -> str:
    url = f"{self.lm_studio_url}/v1/chat/completions"
    
    payload = {
        "model": "local-model",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
```

#### 3. Updated Query Translation
**File**: `backend/fhir_chatbot_service.py` - `translate_to_query()` method

**Changes**:
- Changed from `model.generate_content()` to `_call_lm_studio()`
- Uses OpenAI-compatible message format with system/user roles
- Maintains same prompt structure and validation

#### 4. Updated Answer Synthesis
**File**: `backend/fhir_chatbot_service.py` - `synthesize_answer()` method

**Changes**:
- Changed from Gemini API to LM Studio API
- Uses chat completions endpoint with system and user messages

#### 5. Added Dependencies
**File**: `requirements.txt`

**Added**:
```
requests==2.31.0
```

---

## Agentic Chatbot Enhancements

### Problem
The FHIR chatbot was not robust enough - it failed on complex queries and didn't self-correct when queries returned no results.

### Solution: Implemented Agentic Architecture

#### 1. Planning Phase
**File**: `backend/fhir_chatbot_service.py` - `_plan_query_strategy()` method

**Purpose**: Analyzes question complexity before query generation

**Features**:
- Determines resource type needed
- Assesses complexity (simple/moderate/complex)
- Identifies if multi-step reasoning is needed
- Provides reasoning context for query generation

#### 2. Query Generation with Self-Validation
**File**: `backend/fhir_chatbot_service.py` - `translate_to_query()` method

**Enhancements**:
- Uses planning context to inform query generation
- Validates queries before execution
- Self-corrects on validation failures with error context
- Up to 4 retry attempts with progressive refinement

**Key Changes**:
```python
# Validate and refine if needed
query, is_valid, error_msg = self._validate_and_refine_query(
    query, question, last_error if attempt > 0 else None
)
```

#### 3. Result Validation
**File**: `backend/fhir_chatbot_service.py` - `_validate_results()` method

**Features**:
- Validates results against original question
- Checks if collections exist and have data
- Identifies when queries are too restrictive
- Provides actionable feedback

#### 4. Iterative Query Refinement
**File**: `backend/fhir_chatbot_service.py` - `_refine_query_for_empty_results()` method

**Features**:
- If query returns no results, analyzes sample data
- Generates alternative queries using available fields
- Automatically retries with refined queries
- Tracks refinement attempts in metadata

#### 5. Enhanced Answer Synthesis
**File**: `backend/fhir_chatbot_service.py` - `synthesize_answer()` method

**Enhancements**:
- Uses execution metadata (refinement status, validation results)
- Provides context-aware explanations
- Acknowledges when queries were refined
- Better error messages with actionable guidance

#### 6. Improved Error Recovery
**File**: `backend/fhir_chatbot_service.py` - `chat()` method

**Error Types Handled**:
- Connection errors: Clear messages about LM Studio connectivity
- Timeout errors: Suggests simpler questions
- Validation errors: Provides specific guidance based on error type
- Fallback handling: Graceful degradation with helpful suggestions

---

## Path Resolution Fixes

### Problem
Frontend had hardcoded macOS path `/Users/aritrasanyal/EHR_Test/test_ehr_data.csv` that doesn't work on Windows.

### Solution

#### 1. Removed Hardcoded Paths
**File**: `frontend/src/App.jsx`

**Changes**:
- Line 1525: Changed from `/Users/aritrasanyal/EHR_Test/test_ehr_data.csv` to `test_ehr_data.csv`
- Line 1551: Changed from `/Users/aritrasanyal/EHR_Test/test_ehr_data.csv` to `test_ehr_data.csv`

#### 2. Enhanced Backend Path Resolution
**File**: `backend/ingestion_engine.py` - `_prepare_sources()` method

**Features**:
- Handles relative paths by checking multiple locations:
  1. Original path
  2. Relative to backend directory
  3. Relative to project root
  4. In `data/` folder
  5. In `examples/` folder
- Works on Windows, macOS, and Linux
- Provides clear error messages with all attempted paths

**Implementation**:
```python
if not os.path.isabs(file_path):
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    possible_paths = [
        file_path,
        os.path.join(backend_dir, file_path),
        os.path.join(project_root, file_path),
        os.path.join(project_root, 'data', file_path),
        os.path.join(project_root, 'examples', file_path),
    ]
    
    found_path = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            found_path = path
            break
```

---

## Key Improvements Summary

### Ingestion Jobs
✅ **Fixed**: Records now only show as "Processed" when actually written to MongoDB  
✅ **Added**: Pre-start validation prevents jobs from starting with invalid config  
✅ **Improved**: Error messages are now visible in UI with technical details  
✅ **Enhanced**: Better logging throughout the ingestion process  

### FHIR Chatbot
✅ **Replaced**: Gemini API with LM Studio local inference  
✅ **Added**: Agentic architecture with planning, validation, and self-correction  
✅ **Improved**: Query refinement when no results found  
✅ **Enhanced**: Better error messages and recovery  

### Path Handling
✅ **Fixed**: Removed hardcoded macOS paths  
✅ **Added**: Cross-platform path resolution  
✅ **Improved**: Clear error messages when files not found  

---

## Testing Checklist

### Ingestion Jobs
- [x] Verify records are written to MongoDB when job runs
- [x] Verify `processed` count matches actual MongoDB records
- [x] Verify error messages appear when source data missing
- [x] Verify error messages appear when destination not configured
- [x] Verify CSV file path resolution works on Windows

### FHIR Chatbot
- [x] Verify chatbot connects to LM Studio at `http://127.0.0.1:1234`
- [x] Verify queries are translated correctly
- [x] Verify empty results trigger query refinement
- [x] Verify error messages are helpful and actionable

---

## Configuration

### Environment Variables

**LM Studio URL** (optional):
```bash
LM_STUDIO_URL=http://127.0.0.1:1234
```

**FHIR Chatbot Debug** (optional):
```bash
FHIR_CHATBOT_DEBUG=true
```

### File Locations

**CSV Test Data**:
- Primary location: `test_ehr_data.csv` (project root)
- Alternative locations checked:
  - `backend/test_ehr_data.csv`
  - `data/test_ehr_data.csv`
  - `examples/test_ehr_data.csv`

---

## Notes for Future Development

1. **Ingestion Jobs**: Consider adding file upload capability to UI instead of relying on file paths
2. **Chatbot**: Consider caching LM Studio responses for better performance
3. **Error Handling**: Consider adding retry logic for transient MongoDB connection failures
4. **Path Resolution**: Consider using a configuration file for common file paths

---

## Files Modified

### Backend
- `backend/ingestion_engine.py` - Major refactoring for error handling and validation
- `backend/fhir_chatbot_service.py` - Complete rewrite for LM Studio and agentic architecture
- `requirements.txt` - Added `requests==2.31.0`

### Frontend
- `frontend/src/App.jsx` - Error display, path fixes, infinite loop fixes

---

## Related Documentation

- See `INGESTION_TEST_GUIDE.md` for testing procedures
- See `FHIR_CHATBOT_SUMMARY.md` for chatbot usage
- See `TROUBLESHOOTING.md` for common issues

---

**Last Updated**: 2024-12-19  
**Author**: AI Assistant  
**Status**: ✅ All fixes implemented and tested

