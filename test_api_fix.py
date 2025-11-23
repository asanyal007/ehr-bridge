"""Quick test of fixed API endpoint"""
import requests

API_BASE = 'http://localhost:8000'

# Get token
token = requests.post(f'{API_BASE}/api/v1/auth/demo-token').json()['token']
headers = {'Authorization': f'Bearer {token}'}

# Test reading records
print("Testing fixed API endpoint...")
resp = requests.get(f'{API_BASE}/api/v1/ingestion/jobs/test_read_job_12345/records?limit=10', headers=headers)

print(f"Status Code: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    records = data.get('records', [])
    print(f"SUCCESS! API returned {len(records)} records")
    if records:
        print(f"\nFirst record:")
        print(f"  Patient ID: {records[0].get('patient_id')}")
        print(f"  Name: {records[0].get('first_name')} {records[0].get('last_name')}")
        print(f"  Job ID: {records[0].get('job_id')}")
else:
    print(f"FAILED: {resp.text}")

