#!/usr/bin/env python3
"""
Quick diagnostic script to check what data is in MongoDB
"""
from pymongo import MongoClient
import sys

def check_mongo_data():
    try:
        # Connect to MongoDB
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("[OK] Connected to MongoDB")
        
        # Check 'ehr' database
        db = client['ehr']
        print(f"\n[INFO] Checking database: ehr")
        
        # List all collections
        collections = db.list_collection_names()
        print(f"\n[INFO] Collections found: {collections}")
        
        # Check fhir_Patient collection
        if 'fhir_Patient' in collections:
            patient_coll = db['fhir_Patient']
            patient_count = patient_coll.count_documents({})
            print(f"\n[INFO] fhir_Patient collection: {patient_count} records")
            if patient_count > 0:
                sample = list(patient_coll.find({}).limit(1))
                if sample:
                    print(f"[INFO] Sample Patient record keys: {list(sample[0].keys())}")
        else:
            print(f"\n[WARN] fhir_Patient collection does not exist")
        
        # Check staging collection
        if 'staging' in collections:
            staging_coll = db['staging']
            staging_count = staging_coll.count_documents({})
            print(f"\n[INFO] staging collection: {staging_count} records")
            if staging_count > 0:
                sample = list(staging_coll.find({}).limit(1))
                if sample:
                    print(f"[INFO] Sample staging record keys: {list(sample[0].keys())}")
                    # Check if it has job_id
                    if 'job_id' in sample[0]:
                        print(f"[INFO] Sample job_id: {sample[0]['job_id']}")
        else:
            print(f"\n[WARN] staging collection does not exist")
        
        # Check other fhir_* collections
        fhir_collections = [c for c in collections if c.startswith('fhir_')]
        if fhir_collections:
            print(f"\n[INFO] Other FHIR collections:")
            for coll_name in fhir_collections:
                coll = db[coll_name]
                count = coll.count_documents({})
                print(f"  - {coll_name}: {count} records")
        
        print("\n[SUMMARY]")
        if 'fhir_Patient' in collections:
            patient_count = db['fhir_Patient'].count_documents({})
            if patient_count > 0:
                print(f"✅ FHIR Patient data exists: {patient_count} records")
                print("   The chatbot should be able to query this data.")
            else:
                print("❌ fhir_Patient collection exists but is empty")
                if 'staging' in collections:
                    staging_count = db['staging'].count_documents({})
                    if staging_count > 0:
                        print(f"⚠️  Found {staging_count} records in staging collection")
                        print("   This means data was ingested but not transformed to FHIR format.")
                        print("   Check if your ingestion job has mappings configured.")
        else:
            print("❌ fhir_Patient collection does not exist")
            if 'staging' in collections:
                staging_count = db['staging'].count_documents({})
                if staging_count > 0:
                    print(f"⚠️  Found {staging_count} records in staging collection")
                    print("   Data needs to be transformed to FHIR format.")
        
    except Exception as e:
        print(f"[ERROR] Failed to check MongoDB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_mongo_data()

