"""
Comprehensive Backend API Test Suite
Tests all endpoints with realistic EHR/HL7 data
"""
import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "total": 0,
    "failures": []
}

def log_test(test_name, passed, details=""):
    """Log test result"""
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
        print(f"✅ PASS: {test_name}")
    else:
        test_results["failed"] += 1
        test_results["failures"].append({"test": test_name, "details": details})
        print(f"❌ FAIL: {test_name}")
        if details:
            print(f"   Details: {details}")

def print_separator():
    """Print separator line"""
    print("\n" + "="*80 + "\n")

# =============================================================================
# TEST DATA - Realistic EHR/HL7 Schemas
# =============================================================================

# Test Case 1: Cancer Registry Submission
CANCER_REGISTRY_SOURCE = {
    "patient_first_name": "string",
    "patient_last_name": "string",
    "patient_middle_initial": "string",
    "date_of_birth": "date",
    "medical_record_number": "string",
    "ssn": "string",
    "primary_diagnosis_icd10": "string",
    "diagnosis_date": "date",
    "primary_site_code": "string",
    "histology_code": "string",
    "tumor_grade": "string",
    "tumor_size_mm": "integer",
    "lymph_nodes_positive": "integer",
    "lymph_nodes_examined": "integer",
    "metastasis_at_diagnosis": "boolean"
}

CANCER_REGISTRY_TARGET = {
    "patientFullName": "string",
    "birthDate": "datetime",
    "mrn": "string",
    "socialSecurityNumber": "string",
    "cancerDiagnosisCode": "string",
    "dateOfDiagnosis": "datetime",
    "primaryTumorSite": "string",
    "histologicType": "string",
    "tumorGrade": "string",
    "tumorSizeMillimeters": "integer",
    "regionalNodesPositive": "integer",
    "regionalNodesExamined": "integer",
    "distantMetastasis": "boolean"
}

CANCER_REGISTRY_SAMPLE_DATA = [
    {
        "patient_first_name": "Sarah",
        "patient_last_name": "Johnson",
        "patient_middle_initial": "M",
        "date_of_birth": "1965-03-15",
        "medical_record_number": "MRN123456",
        "ssn": "123-45-6789",
        "primary_diagnosis_icd10": "C50.9",
        "diagnosis_date": "2024-01-15",
        "primary_site_code": "C50.9",
        "histology_code": "8500",
        "tumor_grade": "2",
        "tumor_size_mm": 25,
        "lymph_nodes_positive": 2,
        "lymph_nodes_examined": 8,
        "metastasis_at_diagnosis": False
    }
]

# Test Case 2: HL7 v2 to FHIR
HL7_V2_SOURCE = {
    "PID-5.1": "string",
    "PID-5.2": "string",
    "PID-7": "date",
    "PID-18": "string",
    "PID-11.1": "string",
    "OBR-4.1": "string",
    "OBR-7": "datetime",
    "OBX-3.1": "string",
    "OBX-5": "string",
    "OBX-6.1": "string"
}

FHIR_TARGET = {
    "Patient.name.family": "string",
    "Patient.name.given": "string",
    "Patient.birthDate": "date",
    "Patient.identifier.value": "string",
    "Patient.address.line": "string",
    "DiagnosticReport.code.coding.code": "string",
    "DiagnosticReport.effectiveDateTime": "datetime",
    "Observation.code.coding.code": "string",
    "Observation.valueString": "string",
    "Observation.valueQuantity.unit": "string"
}

HL7_SAMPLE_DATA = [
    {
        "PID-5.1": "Doe",
        "PID-5.2": "John",
        "PID-7": "1980-05-15",
        "PID-18": "MRN987654",
        "PID-11.1": "123 Main St",
        "OBR-4.1": "CBC",
        "OBR-7": "2024-10-11T08:00:00",
        "OBX-3.1": "WBC",
        "OBX-5": "9.2",
        "OBX-6.1": "10*3/uL"
    }
]

# Test Case 3: Lab Results Integration
LAB_RESULTS_SOURCE = {
    "patient_id": "string",
    "specimen_id": "string",
    "test_code_loinc": "string",
    "test_name": "string",
    "result_value": "string",
    "result_unit": "string",
    "reference_range": "string",
    "abnormal_flag": "string",
    "performed_datetime": "datetime"
}

LAB_RESULTS_TARGET = {
    "patientMRN": "string",
    "specimenNumber": "string",
    "loincCode": "string",
    "testDescription": "string",
    "observationValue": "string",
    "unitOfMeasure": "string",
    "normalRange": "string",
    "abnormalIndicator": "string",
    "collectionTimestamp": "datetime"
}

LAB_SAMPLE_DATA = [
    {
        "patient_id": "MRN123456",
        "specimen_id": "SPEC-2024-001234",
        "test_code_loinc": "2951-2",
        "test_name": "Sodium, serum",
        "result_value": "142",
        "result_unit": "mmol/L",
        "reference_range": "135-145",
        "abnormal_flag": "N",
        "performed_datetime": "2024-10-11T08:30:00"
    }
]

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_health_check():
    """Test 1: Health check endpoint"""
    print_separator()
    print("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        log_test(
            "Root endpoint accessible",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        data = response.json()
        log_test(
            "Response contains service name",
            "service" in data,
            f"Response: {json.dumps(data, indent=2)}"
        )
        
        log_test(
            "Version is 2.0.0",
            data.get("version") == "2.0.0",
            f"Version: {data.get('version')}"
        )
        
        # Test detailed health endpoint
        response = requests.get(f"{API_BASE_URL}/api/v1/health")
        log_test(
            "Health endpoint accessible",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        health_data = response.json()
        log_test(
            "Health check shows database status",
            "database" in health_data,
            f"Health: {json.dumps(health_data, indent=2)}"
        )
        
        return True
    except Exception as e:
        log_test("Health check", False, str(e))
        return False

def test_authentication():
    """Test 2: JWT Authentication"""
    print_separator()
    print("TEST 2: JWT Authentication")
    
    try:
        # Test demo token generation
        response = requests.post(f"{API_BASE_URL}/api/v1/auth/demo-token")
        log_test(
            "Demo token generation",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        token_data = response.json()
        log_test(
            "Token response contains token",
            "token" in token_data,
            f"Keys: {list(token_data.keys())}"
        )
        
        log_test(
            "Token response contains userId",
            "userId" in token_data,
            f"userId: {token_data.get('userId')}"
        )
        
        # Test custom user login
        login_data = {
            "userId": "test_user_123",
            "username": "Test Clinical Engineer"
        }
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json=login_data,
            headers=HEADERS
        )
        log_test(
            "Custom user login",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        custom_token_data = response.json()
        token = custom_token_data.get("token")
        userId = custom_token_data.get("userId")
        
        log_test(
            "Custom login returns valid token",
            token is not None and len(token) > 20,
            f"Token length: {len(token) if token else 0}"
        )
        
        return token, userId
    except Exception as e:
        log_test("Authentication", False, str(e))
        return None, None

def test_job_creation(token, userId):
    """Test 3: Job Creation"""
    print_separator()
    print("TEST 3: Job Creation - Cancer Registry")
    
    if not token or not userId:
        log_test("Job creation", False, "No valid token/userId")
        return None
    
    try:
        auth_headers = {
            **HEADERS,
            "Authorization": f"Bearer {token}"
        }
        
        job_data = {
            "userId": userId,
            "sourceSchema": CANCER_REGISTRY_SOURCE,
            "targetSchema": CANCER_REGISTRY_TARGET
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs",
            json=job_data,
            headers=auth_headers
        )
        
        log_test(
            "Job creation returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        job = response.json()
        
        log_test(
            "Job has jobId",
            "jobId" in job,
            f"Job keys: {list(job.keys())}"
        )
        
        log_test(
            "Job status is DRAFT",
            job.get("status") == "DRAFT",
            f"Status: {job.get('status')}"
        )
        
        log_test(
            "Job has correct source schema",
            len(job.get("sourceSchema", {})) == len(CANCER_REGISTRY_SOURCE),
            f"Source fields: {len(job.get('sourceSchema', {}))}"
        )
        
        log_test(
            "Job has correct target schema",
            len(job.get("targetSchema", {})) == len(CANCER_REGISTRY_TARGET),
            f"Target fields: {len(job.get('targetSchema', {}))}"
        )
        
        return job.get("jobId"), auth_headers
    except Exception as e:
        log_test("Job creation", False, str(e))
        return None, None

def test_schema_analysis(jobId, auth_headers, userId):
    """Test 4: AI Schema Analysis with Sentence-BERT"""
    print_separator()
    print("TEST 4: AI Schema Analysis (Sentence-BERT)")
    
    if not jobId or not auth_headers:
        log_test("Schema analysis", False, "No valid jobId/headers")
        return None
    
    try:
        analyze_data = {"userId": userId}
        
        print(f"   Analyzing job: {jobId}")
        print("   This will load the Sentence-BERT model...")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs/{jobId}/analyze",
            json=analyze_data,
            headers=auth_headers,
            timeout=120  # Allow time for model loading
        )
        
        log_test(
            "Analysis returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        job = response.json()
        
        log_test(
            "Job status changed to PENDING_REVIEW",
            job.get("status") == "PENDING_REVIEW",
            f"Status: {job.get('status')}"
        )
        
        suggested_mappings = job.get("suggestedMappings", [])
        
        log_test(
            "AI generated mapping suggestions",
            len(suggested_mappings) > 0,
            f"Suggested mappings: {len(suggested_mappings)}"
        )
        
        if suggested_mappings:
            print(f"\n   📊 AI Suggestions ({len(suggested_mappings)} mappings):")
            for i, mapping in enumerate(suggested_mappings[:5], 1):
                conf = mapping.get('confidenceScore', 0)
                transform = mapping.get('suggestedTransform', 'UNKNOWN')
                print(f"   {i}. {mapping.get('sourceField')} → {mapping.get('targetField')}")
                print(f"      Confidence: {conf*100:.0f}% | Transform: {transform}")
            
            # Test confidence scores
            high_confidence = [m for m in suggested_mappings if m.get('confidenceScore', 0) > 0.7]
            log_test(
                "At least one high-confidence mapping (>70%)",
                len(high_confidence) > 0,
                f"High confidence: {len(high_confidence)}/{len(suggested_mappings)}"
            )
            
            # Test name concatenation detection
            concat_mappings = [m for m in suggested_mappings if m.get('suggestedTransform') == 'CONCAT']
            log_test(
                "Detected name concatenation pattern",
                len(concat_mappings) > 0,
                f"CONCAT mappings: {len(concat_mappings)}"
            )
        
        return job
    except Exception as e:
        log_test("Schema analysis", False, str(e))
        return None

def test_job_approval(jobId, auth_headers, userId, analyzed_job):
    """Test 5: Job Approval"""
    print_separator()
    print("TEST 5: Job Approval")
    
    if not jobId or not auth_headers or not analyzed_job:
        log_test("Job approval", False, "Missing required data")
        return None
    
    try:
        # Get top 5 mappings and approve them
        suggested = analyzed_job.get("suggestedMappings", [])[:5]
        
        # Mark them as approved
        final_mappings = [
            {**mapping, "isApproved": True, "isRejected": False}
            for mapping in suggested
        ]
        
        approval_data = {
            "userId": userId,
            "finalMappings": final_mappings
        }
        
        response = requests.put(
            f"{API_BASE_URL}/api/v1/jobs/{jobId}/approve",
            json=approval_data,
            headers=auth_headers
        )
        
        log_test(
            "Approval returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        job = response.json()
        
        log_test(
            "Job status changed to APPROVED",
            job.get("status") == "APPROVED",
            f"Status: {job.get('status')}"
        )
        
        final = job.get("finalMappings", [])
        log_test(
            "Final mappings saved",
            len(final) > 0,
            f"Final mappings: {len(final)}"
        )
        
        log_test(
            "Correct number of final mappings",
            len(final) == len(final_mappings),
            f"Expected: {len(final_mappings)}, Got: {len(final)}"
        )
        
        return job
    except Exception as e:
        log_test("Job approval", False, str(e))
        return None

def test_transformation(jobId, auth_headers, approved_job):
    """Test 6: Data Transformation"""
    print_separator()
    print("TEST 6: Data Transformation")
    
    if not jobId or not auth_headers or not approved_job:
        log_test("Transformation", False, "Missing required data")
        return
    
    try:
        final_mappings = approved_job.get("finalMappings", [])
        
        transform_data = {
            "mappings": final_mappings,
            "sampleData": CANCER_REGISTRY_SAMPLE_DATA
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs/{jobId}/transform",
            json=transform_data,
            headers=auth_headers
        )
        
        log_test(
            "Transformation returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        result = response.json()
        
        log_test(
            "Transformation result has jobId",
            result.get("jobId") == jobId,
            f"JobId: {result.get('jobId')}"
        )
        
        log_test(
            "Transformation result has source data",
            "sourceData" in result,
            f"Keys: {list(result.keys())}"
        )
        
        log_test(
            "Transformation result has transformed data",
            "transformedData" in result,
            f"Transformed records: {result.get('recordCount', 0)}"
        )
        
        transformed = result.get("transformedData", [])
        log_test(
            "Transformed data has records",
            len(transformed) > 0,
            f"Records: {len(transformed)}"
        )
        
        if transformed:
            print(f"\n   📊 Transformation Results:")
            print(f"   Source record: {CANCER_REGISTRY_SAMPLE_DATA[0].get('patient_first_name')} {CANCER_REGISTRY_SAMPLE_DATA[0].get('patient_last_name')}")
            print(f"   Transformed fields: {list(transformed[0].keys())}")
            print(f"   Sample output: {json.dumps(transformed[0], indent=6)}")
        
    except Exception as e:
        log_test("Transformation", False, str(e))

def test_job_retrieval(jobId, auth_headers):
    """Test 7: Job Retrieval"""
    print_separator()
    print("TEST 7: Job Retrieval")
    
    if not jobId:
        log_test("Job retrieval", False, "No jobId")
        return
    
    try:
        # Test get single job
        response = requests.get(
            f"{API_BASE_URL}/api/v1/jobs/{jobId}",
            headers=auth_headers
        )
        
        log_test(
            "Get single job returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        job = response.json()
        log_test(
            "Retrieved job has correct ID",
            job.get("jobId") == jobId,
            f"JobId: {job.get('jobId')}"
        )
        
        # Test get all jobs
        response = requests.get(
            f"{API_BASE_URL}/api/v1/jobs",
            headers=auth_headers
        )
        
        log_test(
            "Get all jobs returns 200",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        jobs = response.json()
        log_test(
            "Jobs list is array",
            isinstance(jobs, list),
            f"Type: {type(jobs)}"
        )
        
        log_test(
            "Jobs list contains created job",
            any(j.get("jobId") == jobId for j in jobs),
            f"Total jobs: {len(jobs)}"
        )
        
    except Exception as e:
        log_test("Job retrieval", False, str(e))

def test_hl7_to_fhir_workflow(token, userId):
    """Test 8: Complete HL7 to FHIR Workflow"""
    print_separator()
    print("TEST 8: HL7 v2 to FHIR Workflow")
    
    if not token or not userId:
        log_test("HL7 to FHIR workflow", False, "No token/userId")
        return
    
    try:
        auth_headers = {
            **HEADERS,
            "Authorization": f"Bearer {token}"
        }
        
        # Create job
        job_data = {
            "userId": userId,
            "sourceSchema": HL7_V2_SOURCE,
            "targetSchema": FHIR_TARGET
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs",
            json=job_data,
            headers=auth_headers
        )
        
        log_test(
            "HL7 to FHIR job created",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        job = response.json()
        jobId = job.get("jobId")
        
        # Analyze with AI
        analyze_data = {"userId": userId}
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs/{jobId}/analyze",
            json=analyze_data,
            headers=auth_headers,
            timeout=60
        )
        
        log_test(
            "HL7 analysis completed",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        analyzed = response.json()
        mappings = analyzed.get("suggestedMappings", [])
        
        log_test(
            "HL7 AI generated mappings",
            len(mappings) > 0,
            f"Mappings: {len(mappings)}"
        )
        
        # Check for PID segment mappings
        pid_mappings = [m for m in mappings if "PID" in m.get("sourceField", "")]
        log_test(
            "Detected HL7 PID segment mappings",
            len(pid_mappings) > 0,
            f"PID mappings: {len(pid_mappings)}"
        )
        
        print(f"\n   📊 HL7 to FHIR Mappings ({len(mappings)}):")
        for i, m in enumerate(mappings[:3], 1):
            print(f"   {i}. {m.get('sourceField')} → {m.get('targetField')} ({m.get('confidenceScore')*100:.0f}%)")
        
    except Exception as e:
        log_test("HL7 to FHIR workflow", False, str(e))

def test_lab_results_workflow(token, userId):
    """Test 9: Lab Results Integration Workflow"""
    print_separator()
    print("TEST 9: Lab Results Integration Workflow")
    
    if not token or not userId:
        log_test("Lab results workflow", False, "No token/userId")
        return
    
    try:
        auth_headers = {
            **HEADERS,
            "Authorization": f"Bearer {token}"
        }
        
        # Create job
        job_data = {
            "userId": userId,
            "sourceSchema": LAB_RESULTS_SOURCE,
            "targetSchema": LAB_RESULTS_TARGET
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs",
            json=job_data,
            headers=auth_headers
        )
        
        log_test(
            "Lab results job created",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        job = response.json()
        jobId = job.get("jobId")
        
        # Analyze
        analyze_data = {"userId": userId}
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs/{jobId}/analyze",
            json=analyze_data,
            headers=auth_headers,
            timeout=60
        )
        
        log_test(
            "Lab results analysis completed",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        analyzed = response.json()
        mappings = analyzed.get("suggestedMappings", [])
        
        log_test(
            "Lab results AI generated mappings",
            len(mappings) > 0,
            f"Mappings: {len(mappings)}"
        )
        
        # Check for LOINC code mapping
        loinc_mappings = [m for m in mappings if "loinc" in m.get("sourceField", "").lower()]
        log_test(
            "Detected LOINC code mapping",
            len(loinc_mappings) > 0,
            f"LOINC mappings: {len(loinc_mappings)}"
        )
        
        # Approve and transform
        final_mappings = [{**m, "isApproved": True} for m in mappings[:5]]
        approval_data = {"userId": userId, "finalMappings": final_mappings}
        
        response = requests.put(
            f"{API_BASE_URL}/api/v1/jobs/{jobId}/approve",
            json=approval_data,
            headers=auth_headers
        )
        
        log_test(
            "Lab results job approved",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # Test transformation
        approved = response.json()
        transform_data = {
            "mappings": approved.get("finalMappings", []),
            "sampleData": LAB_SAMPLE_DATA
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs/{jobId}/transform",
            json=transform_data,
            headers=auth_headers
        )
        
        log_test(
            "Lab results transformation successful",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        result = response.json()
        print(f"\n   📊 Lab Results Transformation:")
        print(f"   Source: {LAB_SAMPLE_DATA[0].get('test_name')}")
        print(f"   LOINC: {LAB_SAMPLE_DATA[0].get('test_code_loinc')}")
        print(f"   Transformed: {len(result.get('transformedData', []))} records")
        
    except Exception as e:
        log_test("Lab results workflow", False, str(e))

def test_error_handling(token):
    """Test 10: Error Handling"""
    print_separator()
    print("TEST 10: Error Handling")
    
    if not token:
        log_test("Error handling", False, "No token")
        return
    
    try:
        auth_headers = {
            **HEADERS,
            "Authorization": f"Bearer {token}"
        }
        
        # Test invalid job ID
        response = requests.get(
            f"{API_BASE_URL}/api/v1/jobs/invalid_job_id_999",
            headers=auth_headers
        )
        
        log_test(
            "Invalid job ID returns 404",
            response.status_code == 404,
            f"Status: {response.status_code}"
        )
        
        # Test missing auth
        response = requests.get(f"{API_BASE_URL}/api/v1/jobs")
        
        log_test(
            "Missing auth returns 403 or 401",
            response.status_code in [401, 403],
            f"Status: {response.status_code}"
        )
        
        # Test invalid schema
        job_data = {
            "userId": "test",
            "sourceSchema": {},  # Empty schema
            "targetSchema": {}
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs",
            json=job_data,
            headers=auth_headers
        )
        
        # Should still create but with no mappings
        log_test(
            "Empty schema handled gracefully",
            response.status_code in [200, 400, 422],
            f"Status: {response.status_code}"
        )
        
    except Exception as e:
        log_test("Error handling", False, str(e))

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*80)
    print("🏥 AI DATA INTEROPERABILITY PLATFORM - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Starting tests at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {API_BASE_URL}")
    print("="*80)
    
    start_time = time.time()
    
    # Test 1: Health Check
    if not test_health_check():
        print("\n❌ Backend not accessible! Make sure it's running:")
        print("   cd backend && python run.py")
        return
    
    # Test 2: Authentication
    token, userId = test_authentication()
    if not token:
        print("\n❌ Authentication failed! Cannot continue.")
        return
    
    # Test 3-7: Main Cancer Registry Workflow
    jobId, auth_headers = test_job_creation(token, userId)
    if jobId and auth_headers:
        analyzed_job = test_schema_analysis(jobId, auth_headers, userId)
        if analyzed_job:
            approved_job = test_job_approval(jobId, auth_headers, userId, analyzed_job)
            if approved_job:
                test_transformation(jobId, auth_headers, approved_job)
        test_job_retrieval(jobId, auth_headers)
    
    # Test 8: HL7 to FHIR
    test_hl7_to_fhir_workflow(token, userId)
    
    # Test 9: Lab Results
    test_lab_results_workflow(token, userId)
    
    # Test 10: Error Handling
    test_error_handling(token)
    
    # Print summary
    elapsed = time.time() - start_time
    print_separator()
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {test_results['total']}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"Success Rate: {test_results['passed']/test_results['total']*100:.1f}%")
    print(f"Duration: {elapsed:.2f} seconds")
    
    if test_results['failed'] > 0:
        print("\n❌ FAILED TESTS:")
        for failure in test_results['failures']:
            print(f"   - {failure['test']}")
            if failure['details']:
                print(f"     {failure['details']}")
    else:
        print("\n🎉 ALL TESTS PASSED!")
    
    print("="*80)

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()

