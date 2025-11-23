"""
Create a NEW test ingestion job with the fixed code
This will verify the fixes are working
"""
import requests
import json
import time

API_BASE = 'http://localhost:8000'

print("="*70)
print("Creating NEW Test Ingestion Job")
print("="*70)

# 1. Get auth token
print('\n[1/6] Getting auth token...')
resp = requests.post(f'{API_BASE}/api/v1/auth/demo-token')
token = resp.json()['token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
print('   OK - Authenticated')

# 2. Create a simple ingestion job
print('\n[2/6] Creating ingestion job with sample data...')

# Simple job config
job_config = {
    'source_connector': {
        'connector_type': 'csv',
        'config': {
            'file_path': 'sample_data_person.csv',
            'schema': [
                {'name': 'patient_id', 'type': 'string'},
                {'name': 'first_name', 'type': 'string'},
                {'name': 'last_name', 'type': 'string'},
                {'name': 'gender', 'type': 'string'},
                {'name': 'birth_date', 'type': 'string'}
            ]
        }
    },
    'destination_connector': {
        'connector_type': 'mongodb',
        'config': {
            'uri': 'mongodb://localhost:27017',
            'database': 'ehr',
            'collection': 'staging'
        }
    },
    'mappings': [],
    'resource_type': 'Patient'
}

try:
    resp = requests.post(f'{API_BASE}/api/v1/ingestion/jobs', json=job_config, headers=headers)
    if resp.status_code != 200:
        print(f'   ERROR - {resp.status_code}: {resp.text[:200]}')
        print('\n   Trying simplified job creation...')
        # If that fails, try with minimal config
        job_config = {
            'source_connector': {
                'connector_type': 'mongodb',
                'config': {
                    'uri': 'mongodb://localhost:27017',
                    'database': 'ehr',
                    'collection': 'test_source'
                }
            },
            'destination_connector': {
                'connector_type': 'mongodb',
                'config': {
                    'uri': 'mongodb://localhost:27017',
                    'database': 'ehr',
                    'collection': 'staging'
                }
            }
        }
        resp = requests.post(f'{API_BASE}/api/v1/ingestion/jobs', json=job_config, headers=headers)
    
    job_data = resp.json()
    job_id = job_data.get('job_id')
    print(f'   OK - Job created: {job_id}')
except Exception as e:
    print(f'   ERROR - {e}')
    print('\n   Please create the job manually in the UI instead:')
    print('   1. Click "Create Ingestion Job"')
    print('   2. Configure source and destination')
    print('   3. Click "Start"')
    print('   4. Click "View Records" after 10 seconds')
    exit(1)

# 3. Start the job
print(f'\n[3/6] Starting job {job_id}...')
try:
    resp = requests.post(f'{API_BASE}/api/v1/ingestion/jobs/{job_id}/start', headers=headers)
    print(f'   OK - Job started')
except Exception as e:
    print(f'   ERROR - {e}')

# 4. Wait for processing
print('\n[4/6] Waiting for records to process (15 seconds)...')
for i in range(15):
    time.sleep(1)
    print('.', end='', flush=True)
print(' Done')

# 5. Check job status
print(f'\n[5/6] Checking job status...')
try:
    resp = requests.get(f'{API_BASE}/api/v1/ingestion/jobs/{job_id}', headers=headers)
    if resp.status_code == 200:
        status = resp.json().get('job_status', {})
        metrics = status.get('metrics', {})
        print(f'   Status: {status.get("status")}')
        print(f'   Received:  {metrics.get("received", 0)}')
        print(f'   Processed: {metrics.get("processed", 0)}')
        print(f'   Failed:    {metrics.get("failed", 0)}')
except Exception as e:
    print(f'   WARNING - Could not get status: {e}')

# 6. Try to read records
print(f'\n[6/6] Reading records from MongoDB via API...')
try:
    resp = requests.get(f'{API_BASE}/api/v1/ingestion/jobs/{job_id}/records?limit=5', headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        records = data.get('records', [])
        print(f'   Records in MongoDB: {len(records)}')
        
        if len(records) > 0:
            print('\n' + '='*70)
            print('SUCCESS! The fix is working!')
            print('='*70)
            print(f'\nJob ID: {job_id}')
            print(f'Records saved: {len(records)}')
            print(f'\nFirst record:')
            print(json.dumps(records[0], indent=2, default=str)[:300] + '...')
            print('\nYou can now view this job in the UI!')
        else:
            print('\n' + '='*70)
            print('No records yet - may need more time or check backend logs')
            print('='*70)
            print(f'\nJob ID: {job_id}')
            print('Check backend terminal for [ERROR] or [WARNING] messages')
    else:
        print(f'   ERROR - {resp.status_code}: {resp.text}')
except Exception as e:
    print(f'   ERROR - {e}')

print(f'\n\nNEW JOB ID: {job_id}')
print('Go to the UI and look for this job to see records!')

