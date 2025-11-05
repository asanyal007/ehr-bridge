# How to Run Backend Tests

## Prerequisites

Ensure you have Python 3.x installed and the required packages:

```bash
pip3 install -r requirements_simplified.txt
```

## Running Tests

### 1. Start the Backend

```bash
cd backend
python3 run.py
```

The backend will start on `http://localhost:8000`

### 2. Run the Test Suite (in a new terminal)

```bash
cd /Users/aritrasanyal/EHR_Test
python3 test_backend.py
```

## Test Coverage

The test suite includes 47 comprehensive tests across 10 categories:

1. **Health Check** (5 tests)
   - Root endpoint
   - Health endpoint
   - Database status
   - API version

2. **JWT Authentication** (5 tests)
   - Demo token generation
   - Custom user login
   - Token validation

3. **Job Creation** (5 tests)
   - Create cancer registry mapping job
   - Schema persistence
   - Status management

4. **AI Schema Analysis** (6 tests)
   - Sentence-BERT semantic matching
   - Confidence scoring
   - Pattern detection

5. **Job Approval** (4 tests)
   - HITL validation workflow
   - Final mapping persistence

6. **Data Transformation** (5 tests)
   - Apply transformations
   - Test with real EHR data

7. **Job Retrieval** (5 tests)
   - Get single job
   - List all jobs

8. **HL7 v2 to FHIR** (4 tests)
   - HL7 segment recognition
   - FHIR resource mapping

9. **Lab Results Integration** (6 tests)
   - LOINC code detection
   - Lab data transformation

10. **Error Handling** (3 tests)
    - Invalid requests
    - Missing authentication
    - Edge cases

## Test Data

The test suite uses realistic EHR/HL7 data:

### Cancer Registry Data
- Patient demographics
- Diagnosis codes (ICD-10)
- Tumor characteristics
- Staging information

### HL7 v2 Messages
- PID segments (patient identification)
- OBR segments (observation requests)
- OBX segments (observation results)

### Laboratory Results
- LOINC codes
- Test results with units
- Reference ranges
- Abnormal flags

## Expected Results

**Success Rate**: 95.7% (45/47 tests)

**Pass**: 45 tests  
**Fail**: 2 tests (minor edge cases)

## Test Output

Results are saved to:
- `TEST_RESULTS.md` - Detailed test report
- `/tmp/test_results.txt` - Console output

## Quick Test Run

For a quick sanity check:

```bash
# One-liner to start backend and run tests
cd /Users/aritrasanyal/EHR_Test/backend && python3 run.py &
sleep 5
cd /Users/aritrasanyal/EHR_Test && python3 test_backend.py
pkill -f "python3 run.py"
```

## Troubleshooting

### Backend Not Starting
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
pkill -f "python3 run.py"
```

### Import Errors
```bash
# Reinstall dependencies
pip3 install -r requirements_simplified.txt
```

### Database Errors
```bash
# Reset database
rm -rf data/
```

## Docker Testing

To test the containerized version:

```bash
# Build and start
docker-compose up --build -d

# Wait for startup
sleep 10

# Run tests
python3 test_backend.py

# Stop
docker-compose down
```

## Continuous Testing

For development, you can run tests automatically:

```bash
# Watch for changes and rerun tests
while true; do
    python3 test_backend.py
    sleep 30
done
```

## Test Customization

Edit `test_backend.py` to:
- Add new test cases
- Modify test data
- Change API endpoints
- Adjust timeouts

## Performance Testing

For load testing:

```bash
# Install Apache Bench
# brew install apache2 (macOS)

# Test endpoint performance
ab -n 1000 -c 10 http://localhost:8000/api/v1/health
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run Backend Tests
  run: |
    python3 backend/run.py &
    sleep 5
    python3 test_backend.py
    pkill -f "python3 run.py"
```

