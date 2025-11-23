"""
Test Ingestion Pipeline MongoDB Write Fix
Creates a new ingestion job and verifies records are actually saved to MongoDB
"""
import requests
import json
import time

API_BASE = 'http://localhost:8000'

def main():
    print("="*70)
    print("Testing Ingestion Pipeline MongoDB Write Fix")
    print("="*70)
    
    # 1. Get auth token
    print('\n[1/7] Getting auth token...')
    resp = requests.post(f'{API_BASE}/api/v1/auth/demo-token')
    token = resp.json()['token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    print('   OK - Authenticated')

    # 2. Upload CSV to infer schema
    print('\n[2/7] Uploading CSV file (sample_data_person.csv)...')
    try:
        with open('sample_data_person.csv', 'rb') as f:
            files = {'file': ('sample_data_person.csv', f, 'text/csv')}
            resp = requests.post(
                f'{API_BASE}/api/v1/csv/infer-schema', 
                files=files, 
                headers={'Authorization': f'Bearer {token}'}
            )
            schema_data = resp.json()
            num_cols = len(schema_data.get('columns', []))
            print(f'   OK - Schema detected: {num_cols} columns')
    except Exception as e:
        print(f'   ERROR - {e}')
        return

    # 3. Create ingestion job
    print('\n[3/7] Creating ingestion job...')
    job_config = {
        'source_connector': {
            'connector_type': 'csv',
            'config': {
                'file_path': 'sample_data_person.csv',
                'schema': schema_data.get('columns', [])
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

    resp = requests.post(f'{API_BASE}/api/v1/ingestion/jobs', json=job_config, headers=headers)
    if resp.status_code != 200:
        print(f'   ERROR - {resp.status_code}: {resp.text}')
        return
        
    job_data = resp.json()
    job_id = job_data.get('job_id')
    print(f'   OK - Job created: {job_id}')

    # 4. Start the job
    print('\n[4/7] Starting job...')
    resp = requests.post(f'{API_BASE}/api/v1/ingestion/jobs/{job_id}/start', headers=headers)
    print(f'   OK - Job started')

    # 5. Wait for job to process
    print('\n[5/7] Waiting for job to process records (10 seconds)...')
    for i in range(10):
        time.sleep(1)
        print('.', end='', flush=True)
    print(' Done')

    # 6. Check job status
    print('\n[6/7] Checking job status...')
    resp = requests.get(f'{API_BASE}/api/v1/ingestion/jobs/{job_id}', headers=headers)
    status_data = resp.json()
    status = status_data.get('job_status', {})
    metrics = status.get('metrics', {})
    
    print(f'   Job Status: {status.get("status")}')
    print(f'   Metrics:')
    print(f'     - Received:  {metrics.get("received", 0)}')
    print(f'     - Processed: {metrics.get("processed", 0)}')
    print(f'     - Failed:    {metrics.get("failed", 0)}')

    # 7. Check if records are actually in MongoDB
    print('\n[7/7] Checking MongoDB for actual records...')
    resp = requests.get(f'{API_BASE}/api/v1/ingestion/jobs/{job_id}/records?limit=5', headers=headers)
    if resp.status_code != 200:
        print(f'   ERROR - {resp.status_code}: {resp.text}')
        return
        
    records_data = resp.json()
    records = records_data.get('records', [])
    num_records = len(records)
    
    print(f'   Records in MongoDB: {num_records}')
    
    # Verdict
    print('\n' + '='*70)
    if num_records > 0:
        print('SUCCESS! Records are now being saved to MongoDB!')
        print('='*70)
        print(f'\nSample record (first 300 chars):')
        print(json.dumps(records[0], indent=2, default=str)[:300] + '...')
    else:
        print('WARNING: No records found in MongoDB')
        print('='*70)
        print('\nCheck backend logs for any [ERROR] or [WARNING] messages')
    
    print(f'\nTest Job ID: {job_id}')
    print('You can view this job in the UI under "Ingestion Pipelines"')

if __name__ == '__main__':
    main()

