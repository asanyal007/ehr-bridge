"""
Direct MongoDB Check - Verify Records in Database
Bypasses the API and checks MongoDB directly
"""
from pymongo import MongoClient
import json
from datetime import datetime

def main():
    print("="*70)
    print("Direct MongoDB Record Check")
    print("="*70)
    
    # Connect to MongoDB
    print("\n[1/5] Connecting to MongoDB...")
    try:
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print("   OK - Connected to MongoDB")
    except Exception as e:
        print(f"   ERROR - Could not connect to MongoDB: {e}")
        return
    
    # List databases
    print("\n[2/5] Listing databases...")
    try:
        dbs = client.list_database_names()
        print(f"   Databases found: {dbs}")
    except Exception as e:
        print(f"   ERROR - {e}")
        return
    
    # Check 'ehr' database
    print("\n[3/5] Checking 'ehr' database...")
    db = client['ehr']
    collections = db.list_collection_names()
    print(f"   Collections in 'ehr': {collections}")
    
    if not collections:
        print("   WARNING - No collections found in 'ehr' database")
        print("   This means no ingestion jobs have written data yet")
        client.close()
        return
    
    # Check each collection for records
    print("\n[4/5] Checking record counts in each collection...")
    collection_stats = {}
    for coll_name in collections:
        coll = db[coll_name]
        count = coll.count_documents({})
        collection_stats[coll_name] = count
        print(f"   {coll_name}: {count} records")
    
    # Show sample records from collections that have data
    print("\n[5/5] Sample records from collections with data...")
    found_data = False
    
    for coll_name, count in collection_stats.items():
        if count > 0:
            found_data = True
            print(f"\n   Collection: {coll_name} ({count} records)")
            print("   " + "-"*66)
            
            coll = db[coll_name]
            
            # Get sample record
            sample = coll.find_one()
            if sample:
                # Remove _id for cleaner display
                sample.pop('_id', None)
                
                # Show job_id if present
                if 'job_id' in sample:
                    print(f"   Job ID: {sample['job_id']}")
                
                # Show timestamp if present
                if 'ingested_at' in sample:
                    print(f"   Ingested At: {sample['ingested_at']}")
                elif 'failed_at' in sample:
                    print(f"   Failed At: {sample['failed_at']}")
                elif 'persisted_at' in sample:
                    print(f"   Persisted At: {sample['persisted_at']}")
                
                # Show record content (truncated)
                print(f"\n   Sample Record:")
                record_json = json.dumps(sample, indent=4, default=str)
                if len(record_json) > 500:
                    print("   " + record_json[:500] + "...")
                else:
                    print("   " + record_json)
            
            # List unique job_ids in this collection
            job_ids = coll.distinct('job_id')
            if job_ids:
                print(f"\n   Unique Job IDs in this collection: {job_ids}")
    
    if not found_data:
        print("\n   No data found in any collections")
        print("   This confirms no records have been written to MongoDB yet")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if found_data:
        print("[SUCCESS] Data found in MongoDB!")
        print(f"\nTotal collections with data: {sum(1 for c in collection_stats.values() if c > 0)}")
        print(f"Total records across all collections: {sum(collection_stats.values())}")
        print("\nCollections:")
        for coll_name, count in collection_stats.items():
            if count > 0:
                status = "[OK]"
            else:
                status = "[EMPTY]"
            print(f"  {status} {coll_name}: {count} records")
    else:
        print("[WARNING] No data found in MongoDB")
        print("\nPossible reasons:")
        print("  1. No ingestion jobs have been run yet")
        print("  2. Ingestion jobs failed to write (check backend logs)")
        print("  3. MongoDB connection issues during ingestion")
        print("\nNext steps:")
        print("  - Create a new ingestion job in the UI")
        print("  - Watch backend logs for [ERROR] or [WARNING] messages")
        print("  - Run this script again after the job completes")
    
    client.close()

if __name__ == '__main__':
    main()

