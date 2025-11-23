"""
Test Record Reading Functionality
1. Insert test records directly into MongoDB
2. Try to read them back via the API
3. Verify the API read functionality works
"""
from pymongo import MongoClient
import requests
import json
from datetime import datetime

API_BASE = 'http://localhost:8000'

def main():
    print("="*70)
    print("Testing Record Reading Functionality")
    print("="*70)
    
    # Step 1: Connect to MongoDB and insert test records
    print("\n[1/4] Inserting test records directly into MongoDB...")
    try:
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("   OK - Connected to MongoDB")
        
        db = client['ehr']
        staging_coll = db['staging']
        
        # Create test job_id
        test_job_id = 'test_read_job_12345'
        
        # Insert 3 test records
        test_records = [
            {
                'job_id': test_job_id,
                'ingested_at': datetime.utcnow(),
                'patient_id': 'P001',
                'first_name': 'John',
                'last_name': 'Doe',
                'gender': 'male',
                'test_field': 'This is a test record #1'
            },
            {
                'job_id': test_job_id,
                'ingested_at': datetime.utcnow(),
                'patient_id': 'P002',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'gender': 'female',
                'test_field': 'This is a test record #2'
            },
            {
                'job_id': test_job_id,
                'ingested_at': datetime.utcnow(),
                'patient_id': 'P003',
                'first_name': 'Bob',
                'last_name': 'Johnson',
                'gender': 'male',
                'test_field': 'This is a test record #3'
            }
        ]
        
        result = staging_coll.insert_many(test_records)
        print(f"   OK - Inserted {len(result.inserted_ids)} test records")
        print(f"   Test Job ID: {test_job_id}")
        
    except Exception as e:
        print(f"   ERROR - Could not insert test records: {e}")
        return
    
    # Step 2: Verify records are in MongoDB
    print("\n[2/4] Verifying records are in MongoDB...")
    try:
        count = staging_coll.count_documents({'job_id': test_job_id})
        print(f"   OK - Found {count} records in MongoDB for job {test_job_id}")
        
        # Show a sample
        sample = staging_coll.find_one({'job_id': test_job_id})
        if sample:
            sample.pop('_id', None)
            print(f"   Sample record: {json.dumps(sample, indent=2, default=str)[:200]}...")
    except Exception as e:
        print(f"   ERROR - {e}")
        return
    
    # Step 3: Get auth token
    print("\n[3/4] Getting API auth token...")
    try:
        resp = requests.post(f'{API_BASE}/api/v1/auth/demo-token')
        token = resp.json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        print("   OK - Authenticated")
    except Exception as e:
        print(f"   ERROR - Could not get auth token: {e}")
        return
    
    # Step 4: Try to read records via API
    print("\n[4/4] Reading records via API...")
    try:
        url = f'{API_BASE}/api/v1/ingestion/jobs/{test_job_id}/records?limit=10'
        print(f"   API URL: {url}")
        
        resp = requests.get(url, headers=headers)
        print(f"   Response Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            records = data.get('records', [])
            print(f"   OK - API returned {len(records)} records")
            
            if len(records) > 0:
                print(f"\n   First record from API:")
                print(f"   {json.dumps(records[0], indent=2, default=str)[:300]}...")
            else:
                print("   WARNING - API returned 0 records (but MongoDB has records!)")
                print(f"   Full API response: {json.dumps(data, indent=2)}")
        else:
            print(f"   ERROR - API returned status {resp.status_code}")
            print(f"   Response: {resp.text}")
            
    except Exception as e:
        print(f"   ERROR - API request failed: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    # Check both MongoDB and API
    mongo_count = staging_coll.count_documents({'job_id': test_job_id})
    
    try:
        resp = requests.get(f'{API_BASE}/api/v1/ingestion/jobs/{test_job_id}/records?limit=10', headers=headers)
        if resp.status_code == 200:
            api_count = len(resp.json().get('records', []))
        else:
            api_count = 0
    except:
        api_count = 0
    
    print(f"\nRecords in MongoDB (direct):  {mongo_count}")
    print(f"Records from API (via code):  {api_count}")
    
    if mongo_count > 0 and api_count > 0 and mongo_count == api_count:
        print("\n[SUCCESS] Read functionality is WORKING!")
        print("The API can successfully read records from MongoDB.")
    elif mongo_count > 0 and api_count == 0:
        print("\n[PROBLEM] Read functionality is BROKEN!")
        print("Records exist in MongoDB but API cannot read them.")
        print("This indicates a bug in the API endpoint code.")
    elif mongo_count == 0:
        print("\n[INFO] No test records found")
        print("Test records may not have been inserted properly.")
    else:
        print(f"\n[WARNING] Mismatch: MongoDB has {mongo_count}, API returned {api_count}")
    
    # Cleanup
    print("\n" + "="*70)
    cleanup = input("\nDelete test records from MongoDB? (y/n): ")
    if cleanup.lower() == 'y':
        result = staging_coll.delete_many({'job_id': test_job_id})
        print(f"Deleted {result.deleted_count} test records")
    else:
        print(f"Test records kept in MongoDB (job_id: {test_job_id})")
    
    client.close()

if __name__ == '__main__':
    main()

