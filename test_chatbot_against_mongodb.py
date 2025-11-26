#!/usr/bin/env python3
"""
Test FHIR Chatbot against MongoDB Ground Truth
Tests chatbot queries and compares results with actual MongoDB data
"""
import httpx
import json
from pymongo import MongoClient
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "ehr"
TEST_QUESTIONS = [
    "How many patients do we have?",
    "Show me all patients",
    "How many Patient records are in the database?",
    "What patients do we have?",
]

def get_mongodb_ground_truth():
    """Get ground truth data directly from MongoDB"""
    print("\n" + "="*80)
    print("STEP 1: Getting Ground Truth from MongoDB")
    print("="*80)
    
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("[OK] Connected to MongoDB")
        
        db = client[MONGO_DB]
        
        # Check fhir_Patient collection
        collections = db.list_collection_names()
        print(f"\n[INFO] Available collections: {collections}")
        
        ground_truth = {
            "fhir_Patient": None,
            "staging": None,
            "collections_found": collections
        }
        
        # Check fhir_Patient
        if 'fhir_Patient' in collections:
            patient_coll = db['fhir_Patient']
            count = patient_coll.count_documents({})
            ground_truth["fhir_Patient"] = {
                "exists": True,
                "count": count,
                "sample": None
            }
            if count > 0:
                sample = list(patient_coll.find({}).limit(1))
                if sample:
                    # Remove _id for cleaner output
                    sample[0].pop('_id', None)
                    ground_truth["fhir_Patient"]["sample"] = sample[0]
                    print(f"[OK] fhir_Patient: {count} records found")
                    print(f"[INFO] Sample record keys: {list(sample[0].keys())}")
            else:
                print(f"[WARN] fhir_Patient: Collection exists but is empty")
        else:
            ground_truth["fhir_Patient"] = {
                "exists": False,
                "count": 0,
                "sample": None
            }
            print(f"[WARN] fhir_Patient: Collection does not exist")
        
        # Check staging collection
        if 'staging' in collections:
            staging_coll = db['staging']
            count = staging_coll.count_documents({})
            ground_truth["staging"] = {
                "exists": True,
                "count": count,
                "sample": None
            }
            if count > 0:
                sample = list(staging_coll.find({}).limit(1))
                if sample:
                    sample[0].pop('_id', None)
                    ground_truth["staging"]["sample"] = sample[0]
                    print(f"[INFO] staging: {count} records found")
                    print(f"[INFO] Sample staging keys: {list(sample[0].keys())}")
        else:
            ground_truth["staging"] = {
                "exists": False,
                "count": 0,
                "sample": None
            }
        
        return ground_truth
        
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {e}")
        return None

def test_chatbot_query(question, token=None):
    """Test chatbot with a question"""
    try:
        url = f"{API_BASE_URL}/api/v1/chat/query"
        headers = {
            "Content-Type": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        payload = {
            "question": question
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"[ERROR] Chatbot query failed: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"[ERROR] Response: {e.response.text}")
        return None

def get_auth_token():
    """Get demo auth token"""
    try:
        url = f"{API_BASE_URL}/api/v1/auth/demo-token"
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url)
            response.raise_for_status()
            data = response.json()
            return data.get('token')
    except Exception as e:
        print(f"[WARN] Failed to get auth token: {e}")
        return None

def analyze_results(question, chatbot_result, ground_truth):
    """Analyze chatbot results against ground truth"""
    print(f"\n{'='*80}")
    print(f"ANALYSIS: '{question}'")
    print("="*80)
    
    if not chatbot_result:
        print("[FAIL] Chatbot returned no result")
        return False
    
    answer = chatbot_result.get('answer', '')
    results_count = chatbot_result.get('results_count', 0)
    query_used = chatbot_result.get('query_used', {})
    metadata = chatbot_result.get('metadata', {})
    
    print(f"\n[Chatbot Answer]:")
    print(f"  {answer}")
    print(f"\n[Chatbot Results Count]: {results_count}")
    print(f"\n[Query Used]:")
    print(f"  {json.dumps(query_used, indent=2)}")
    
    if metadata:
        print(f"\n[Metadata]:")
        print(f"  {json.dumps(metadata, indent=2)}")
    
    # Compare with ground truth
    print(f"\n[Ground Truth Comparison]:")
    fhir_count = ground_truth.get("fhir_Patient", {}).get("count", 0)
    staging_count = ground_truth.get("staging", {}).get("count", 0)
    
    print(f"  MongoDB fhir_Patient count: {fhir_count}")
    print(f"  MongoDB staging count: {staging_count}")
    print(f"  Chatbot results count: {results_count}")
    
    # Determine if result is correct
    is_correct = False
    issues = []
    
    if fhir_count > 0:
        # If there are FHIR records, chatbot should find them
        if results_count == fhir_count:
            is_correct = True
            print(f"\n[PASS] [OK] Chatbot found correct number of records ({results_count})")
        elif results_count == 0:
            issues.append(f"Chatbot found 0 records but MongoDB has {fhir_count} records in fhir_Patient")
            print(f"\n[FAIL] [X] Chatbot found 0 records but should find {fhir_count}")
        else:
            issues.append(f"Chatbot found {results_count} records but MongoDB has {fhir_count}")
            print(f"\n[WARN] [!] Count mismatch: Chatbot={results_count}, MongoDB={fhir_count}")
    elif staging_count > 0 and fhir_count == 0:
        # Data is in staging but not transformed to FHIR
        issues.append(f"Data exists in staging ({staging_count} records) but not in fhir_Patient. Transformation may not have occurred.")
        print(f"\n[INFO] [i] Data in staging but not in fhir_Patient")
        print(f"        This explains why chatbot can't find Patient records")
        print(f"        Ingestion job may need mappings to transform data to FHIR")
    else:
        issues.append("No data found in either fhir_Patient or staging collections")
        print(f"\n[INFO] [i] No data found in MongoDB")
    
    return {
        "question": question,
        "is_correct": is_correct,
        "issues": issues,
        "chatbot_count": results_count,
        "mongodb_fhir_count": fhir_count,
        "mongodb_staging_count": staging_count,
        "answer": answer
    }

def main():
    print("\n" + "="*80)
    print("FHIR Chatbot Test Against MongoDB Ground Truth")
    print("="*80)
    print(f"API URL: {API_BASE_URL}")
    print(f"MongoDB URI: {MONGO_URI}")
    print(f"Database: {MONGO_DB}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    # Step 1: Get ground truth
    ground_truth = get_mongodb_ground_truth()
    if not ground_truth:
        print("\n[ERROR] Cannot proceed without MongoDB connection")
        return
    
    # Step 2: Get auth token
    print("\n" + "="*80)
    print("STEP 2: Getting Authentication Token")
    print("="*80)
    token = get_auth_token()
    if token:
        print("[OK] Got authentication token")
    else:
        print("[WARN] No auth token, trying without authentication")
    
    # Step 3: Test each question
    print("\n" + "="*80)
    print("STEP 3: Testing Chatbot Queries")
    print("="*80)
    
    results = []
    for question in TEST_QUESTIONS:
        print(f"\n[Testing]: '{question}'")
        chatbot_result = test_chatbot_query(question, token)
        analysis = analyze_results(question, chatbot_result, ground_truth)
        results.append(analysis)
    
    # Step 4: Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results if r["is_correct"])
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"\nGround Truth:")
    print(f"  fhir_Patient records: {ground_truth.get('fhir_Patient', {}).get('count', 0)}")
    print(f"  staging records: {ground_truth.get('staging', {}).get('count', 0)}")
    
    print(f"\nDetailed Results:")
    for i, result in enumerate(results, 1):
        status = "[OK] PASS" if result["is_correct"] else "[X] FAIL"
        print(f"\n{i}. {status} - '{result['question']}'")
        print(f"   Chatbot: {result['chatbot_count']} records")
        print(f"   MongoDB fhir_Patient: {result['mongodb_fhir_count']} records")
        if result['issues']:
            for issue in result['issues']:
                print(f"   [!] {issue}")
    
    # Diagnostic recommendations
    print("\n" + "="*80)
    print("DIAGNOSTIC RECOMMENDATIONS")
    print("="*80)
    
    fhir_count = ground_truth.get('fhir_Patient', {}).get('count', 0)
    staging_count = ground_truth.get('staging', {}).get('count', 0)
    
    if fhir_count == 0 and staging_count > 0:
        print("\n[ISSUE IDENTIFIED]:")
        print("   Data exists in 'staging' collection but not in 'fhir_Patient' collection.")
        print("\n[SOLUTION]:")
        print("   1. Check your ingestion job configuration")
        print("   2. Ensure the ingestion job has a mapping_job_id linked to an approved mapping job")
        print("   3. The ingestion job needs mappings to transform CSV data to FHIR format")
        print("   4. Without mappings, data stays in 'staging' and chatbot can't query it")
    elif fhir_count > 0:
        print("\n[ISSUE IDENTIFIED]:")
        print("   Data exists in 'fhir_Patient' but chatbot is not finding it.")
        print("\n[POSSIBLE CAUSES]:")
        print("   1. Chatbot may be querying wrong database/collection")
        print("   2. Query translation may be incorrect")
        print("   3. MongoDB connection issue in chatbot service")
        print("\n[CHECK]:")
        print("   - Verify chatbot service is using correct MongoDB database name")
        print("   - Check chatbot service logs for query details")
        print("   - Verify MongoDB client connection in chatbot service")
    else:
        print("\n[ISSUE IDENTIFIED]:")
        print("   No data found in MongoDB.")
        print("\n[SOLUTION]:")
        print("   1. Run an ingestion job to load data")
        print("   2. Verify ingestion job completed successfully")
        print("   3. Check ingestion job status and metrics")

if __name__ == "__main__":
    main()

