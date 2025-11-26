#!/usr/bin/env python3
"""
Test staging collection query directly
"""
from pymongo import MongoClient

def test_staging_query():
    try:
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("[OK] Connected to MongoDB")
        
        db = client['ehr']
        
        # Test the exact query the chatbot would use
        staging_filter = {'resourceType': 'Patient'}
        print(f"\n[TEST] Query filter: {staging_filter}")
        
        if 'staging' in db.list_collection_names():
            collection = db['staging']
            
            # Count with resourceType filter
            count = collection.count_documents(staging_filter)
            print(f"[RESULT] Count with resourceType='Patient': {count}")
            
            # Count all records
            total = collection.count_documents({})
            print(f"[RESULT] Total records in staging: {total}")
            
            # Check what resourceTypes exist
            print(f"\n[INFO] Checking resourceType values in staging...")
            pipeline = [
                {"$group": {"_id": "$resourceType", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            resource_types = list(collection.aggregate(pipeline))
            print(f"[RESULT] Resource types in staging:")
            for rt in resource_types:
                print(f"  {rt['_id']}: {rt['count']} records")
            
            # Get a sample record
            sample = collection.find_one(staging_filter)
            if sample:
                print(f"\n[INFO] Sample Patient record keys: {list(sample.keys())}")
                print(f"[INFO] Sample resourceType value: {sample.get('resourceType')}")
                print(f"[INFO] Sample resourceType type: {type(sample.get('resourceType'))}")
            else:
                print(f"\n[WARN] No Patient records found with filter {staging_filter}")
                # Try without filter
                any_sample = collection.find_one({})
                if any_sample:
                    print(f"[INFO] Sample record (any): keys={list(any_sample.keys())}")
                    print(f"[INFO] Sample resourceType: {any_sample.get('resourceType')}")
                    print(f"[INFO] Sample resourceType type: {type(any_sample.get('resourceType'))}")
        else:
            print("[ERROR] staging collection does not exist")
            
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_staging_query()

