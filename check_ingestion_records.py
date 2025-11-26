#!/usr/bin/env python3
"""
Check where ingestion job records are stored
"""
from pymongo import MongoClient
import sys

def check_ingestion_records(job_id):
    try:
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print(f"[OK] Connected to MongoDB")
        
        db = client['ehr']
        
        # Check staging collection for this job
        staging_coll = db['staging']
        staging_count = staging_coll.count_documents({"job_id": job_id})
        print(f"\n[INFO] staging collection (job_id={job_id}): {staging_count} records")
        
        if staging_count > 0:
            sample = list(staging_coll.find({"job_id": job_id}).limit(1))
            if sample:
                print(f"[INFO] Sample staging record keys: {list(sample[0].keys())}")
                if 'resourceType' in sample[0]:
                    print(f"[INFO] Sample has resourceType: {sample[0]['resourceType']}")
                else:
                    print(f"[WARN] Sample does NOT have resourceType - data is not in FHIR format")
        
        # Check fhir_Patient collection for this job
        patient_coll = db['fhir_Patient']
        patient_count = patient_coll.count_documents({"job_id": job_id})
        print(f"\n[INFO] fhir_Patient collection (job_id={job_id}): {patient_count} records")
        
        # Also check total counts
        total_staging = staging_coll.count_documents({})
        total_patient = patient_coll.count_documents({})
        print(f"\n[INFO] Total records:")
        print(f"  staging: {total_staging}")
        print(f"  fhir_Patient: {total_patient}")
        
        # Check all collections
        collections = db.list_collection_names()
        fhir_collections = [c for c in collections if c.startswith('fhir_')]
        print(f"\n[INFO] All FHIR collections:")
        for coll_name in fhir_collections:
            coll = db[coll_name]
            count = coll.count_documents({})
            # Try to count by job_id if collection has records
            job_count = 0
            if count > 0:
                sample = coll.find_one({})
                if sample and 'job_id' in sample:
                    job_count = coll.count_documents({"job_id": job_id})
            print(f"  {coll_name}: {count} total, {job_count} from job {job_id}")
        
        # Diagnosis
        print(f"\n[DIAGNOSIS]:")
        if patient_count > 0:
            print(f"  [OK] Records are in fhir_Patient collection - chatbot should be able to query them")
        elif staging_count > 0:
            print(f"  [ISSUE] Records are in staging but NOT in fhir_Patient")
            print(f"  [CAUSE] Data was ingested but not transformed to FHIR format")
            print(f"  [SOLUTION] Ingestion job needs mappings to transform CSV to FHIR")
            print(f"             Check if ingestion job has mapping_job_id configured")
        else:
            print(f"  [ISSUE] No records found for this job in either collection")
            print(f"  [POSSIBLE CAUSES]")
            print(f"    - Records were written to a different database")
            print(f"    - Records were written to a different collection")
            print(f"    - Job ID mismatch")
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    job_id = sys.argv[1] if len(sys.argv) > 1 else "job_1764117845"
    print(f"Checking records for job: {job_id}")
    check_ingestion_records(job_id)

