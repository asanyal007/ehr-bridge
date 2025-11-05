#!/usr/bin/env python3
"""
Create a simple sample job for testing concept normalization.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager


def create_sample_job():
    """Create a simple sample job directly in the database"""
    
    db = get_db_manager()
    
    # Create job data with all required fields
    job_data = {
        "jobId": "sample_job_001",
        "jobName": "Sample FHIR to OMOP Test Job",
        "sourceConnector": {
            "type": "CSV",
            "config": {
                "file_path": "sample_data.csv"
            }
        },
        "destinationConnector": {
            "type": "FHIR",
            "config": {
                "resource_type": "Patient"
            }
        },
        "sourceSchema": {
            "patient_id": "string",
            "first_name": "string", 
            "last_name": "string",
            "gender": "string",
            "birth_date": "string",
            "mrn": "string"
        },
        "targetSchema": {
            "id": "string",
            "name": "object",
            "gender": "string",
            "birthDate": "string",
            "identifier": "array"
        },
        "status": "APPROVED",
        "finalMappings": [
            {
                "sourceField": "patient_id",
                "targetField": "id",
                "transformationType": "DIRECT",
                "confidenceScore": 0.95,
                "suggestedTransform": "DIRECT"
            },
            {
                "sourceField": "first_name",
                "targetField": "name[0].given[0]",
                "transformationType": "DIRECT",
                "confidenceScore": 0.95,
                "suggestedTransform": "DIRECT"
            },
            {
                "sourceField": "last_name", 
                "targetField": "name[0].family",
                "transformationType": "DIRECT",
                "confidenceScore": 0.95,
                "suggestedTransform": "DIRECT"
            },
            {
                "sourceField": "gender",
                "targetField": "gender",
                "transformationType": "DIRECT",
                "confidenceScore": 0.95,
                "suggestedTransform": "DIRECT"
            },
            {
                "sourceField": "birth_date",
                "targetField": "birthDate",
                "transformationType": "DIRECT",
                "confidenceScore": 0.95,
                "suggestedTransform": "DIRECT"
            },
            {
                "sourceField": "mrn",
                "targetField": "identifier[0].value",
                "transformationType": "DIRECT",
                "confidenceScore": 0.95,
                "suggestedTransform": "DIRECT"
            }
        ],
        "userId": "test_user",
        "createdBy": "test_user",
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat()
    }
    
    try:
        # Check if job already exists
        existing_job = db.get_job("sample_job_001")
        if existing_job:
            print("ℹ️ Sample job already exists")
            return True
        
        # Insert directly into database
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO mapping_jobs 
                (jobId, jobName, sourceConnector, destinationConnector, sourceSchema, 
                 targetSchema, status, finalMappings, userId, createdBy, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_data["jobId"],
                job_data["jobName"],
                str(job_data["sourceConnector"]),
                str(job_data["destinationConnector"]),
                str(job_data["sourceSchema"]),
                str(job_data["targetSchema"]),
                job_data["status"],
                str(job_data["finalMappings"]),
                job_data["userId"],
                job_data["createdBy"],
                job_data["createdAt"],
                job_data["updatedAt"]
            ))
        
        print("✅ Created sample mapping job: sample_job_001")
        return True
        
    except Exception as e:
        print(f"⚠️ Error creating sample job: {e}")
        return False


def main():
    """Main function"""
    print("🚀 Creating sample job for concept normalization testing...")
    
    if create_sample_job():
        print("\n✅ Sample job creation complete!")
        print("\n📋 Next steps:")
        print("1. Go to the Data Model screen")
        print("2. Select the 'sample_job_001' job")
        print("3. Click on OMOP tab")
        print("4. Click 'Predict OMOP Table'")
        print("5. Click 'Normalize Concepts' to see concept suggestions")
        print("6. Click 'Review Concepts' to see the HITL interface")
    else:
        print("❌ Failed to create sample job")


if __name__ == "__main__":
    main()
