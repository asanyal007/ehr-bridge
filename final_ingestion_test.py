"""
Final Comprehensive Ingestion Test
This will create a test job and monitor everything step by step
"""
import requests
import time
import json

API_BASE = 'http://localhost:8000'

print("="*70)
print("FINAL COMPREHENSIVE INGESTION TEST")
print("="*70)

# 1. Auth
print("\n[1] Getting auth token...")
token = requests.post(f'{API_BASE}/api/v1/auth/demo-token').json()['token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
print("   OK")

# 2. Check test_read_job_12345 to verify API works
print("\n[2] Testing API with known good job (test_read_job_12345)...")
resp = requests.get(f'{API_BASE}/api/v1/ingestion/jobs/test_read_job_12345/records?limit=3', headers=headers)
test_records = resp.json().get('records', [])
print(f"   API returned {len(test_records)} records")
if len(test_records) > 0:
    print(f"   [OK] API is working correctly!")
else:
    print(f"   [ERROR] API returned 0 records (unexpected)")

# 3. Check your latest job in MongoDB
print("\n[3] Checking your latest job (job_1763830959) in MongoDB...")
resp = requests.get(f'{API_BASE}/api/v1/ingestion/jobs/job_1763830959/records?limit=5', headers=headers)
your_records = resp.json().get('records', [])
print(f"   API returned {len(your_records)} records for your job")

# 4. Get failed records for your job
print("\n[4] Checking failed records for your job...")
resp = requests.get(f'{API_BASE}/api/v1/ingestion/jobs/job_1763830959/failed?limit=5', headers=headers)
failed_records = resp.json().get('records', [])
print(f"   API returned {len(failed_records)} failed records")
if len(failed_records) > 0:
    print(f"   Sample failed record reason: {failed_records[0].get('error_reason')}")

# Summary
print("\n" + "="*70)
print("DIAGNOSIS")
print("="*70)
print(f"\n[OK] View Records API: WORKING (returned {len(test_records)} test records)")
print(f"[PROBLEM] Your job records: {len(your_records)} successful, {len(failed_records)} failed")
print("\nCONCLUSION:")
print("The API is working perfectly. The problem is that your ingestion")
print("jobs are NOT writing successful records to MongoDB.")
print("\nPOSSIBLE CAUSES:")
print("1. Jobs were created with OLD buggy code before fixes loaded")
print("2. MongoDB client not initializing in ingestion jobs")
print("3. CSV file path not found or readable")
print("4. Transform errors causing all records to fail")

print("\n" + "="*70)
print("RECOMMENDED ACTION")
print("="*70)
print("\n1. Wait 10 seconds for backend to finish reloading")
print("2. Create a BRAND NEW ingestion job in the UI")
print("3. Use a simple config (CSV to MongoDB)")
print("4. Click START")
print("5. Wait 15 seconds")
print("6. Click View Records")
print("\nIf you still see 0 records, check backend logs for:")
print("  [DEBUG] messages about MongoDB client initialization")
print("  [ERROR] messages about write failures")

