#!/usr/bin/env python3
"""
Load sample FHIR resources for testing concept normalization.

This script loads sample FHIR resources into MongoDB to test the
concept normalization and review features.
"""

import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mongodb_client import get_mongo_client
from fhir_id_service import generate_fhir_id


def load_sample_fhir_resources():
    """Load sample FHIR resources into MongoDB"""
    
    # Load sample data
    sample_file = os.path.join(os.path.dirname(__file__), '..', '..', 'test_data', 'sample_fhir_resources.json')
    
    if not os.path.exists(sample_file):
        print(f"❌ Sample data file not found: {sample_file}")
        return False
    
    with open(sample_file, 'r') as f:
        resources = json.load(f)
    
    print(f"📊 Loading {len(resources)} sample FHIR resources...")
    
    # Get MongoDB client
    mongo_client = get_mongo_client()
    db = mongo_client.client['ehr']
    
    # Group resources by type
    resource_groups = {}
    for resource in resources:
        resource_type = resource.get('resourceType')
        if resource_type not in resource_groups:
            resource_groups[resource_type] = []
        resource_groups[resource_type].append(resource)
    
    # Load each resource type
    total_loaded = 0
    for resource_type, resources_list in resource_groups.items():
        collection_name = f"fhir_{resource_type}"
        collection = db[collection_name]
        
        print(f"📝 Loading {len(resources_list)} {resource_type} resources...")
        
        for resource in resources_list:
            # Generate deterministic FHIR ID
            fhir_id = generate_fhir_id(resource)
            resource['id'] = fhir_id
            
            # Add metadata
            resource['job_id'] = 'sample_job_001'
            resource['persisted_at'] = datetime.utcnow()
            
            # Add meta information
            if 'meta' not in resource:
                resource['meta'] = {}
            resource['meta']['lastUpdated'] = datetime.utcnow().isoformat()
            
            # Upsert the resource
            collection.update_one(
                {'id': fhir_id},
                {'$set': resource},
                upsert=True
            )
            
            total_loaded += 1
    
    print(f"✅ Successfully loaded {total_loaded} FHIR resources")
    
    # Print summary
    print("\n📋 Resource Summary:")
    for resource_type, count in resource_groups.items():
        print(f"  - {resource_type}: {count} resources")
    
    return True


def create_sample_mapping_job():
    """Create a sample mapping job for testing"""
    
    from database import get_db_manager
    
    db = get_db_manager()
    
    # Create a sample mapping job
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
        "status": "APPROVED",
        "finalMappings": [
            {
                "sourceField": "patient_id",
                "targetField": "id",
                "transformationType": "DIRECT"
            },
            {
                "sourceField": "first_name",
                "targetField": "name[0].given[0]",
                "transformationType": "DIRECT"
            },
            {
                "sourceField": "last_name", 
                "targetField": "name[0].family",
                "transformationType": "DIRECT"
            },
            {
                "sourceField": "gender",
                "targetField": "gender",
                "transformationType": "DIRECT"
            },
            {
                "sourceField": "birth_date",
                "targetField": "birthDate",
                "transformationType": "DIRECT"
            },
            {
                "sourceField": "mrn",
                "targetField": "identifier[0].value",
                "transformationType": "DIRECT"
            }
        ],
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
        
        # Create the job
        from models import MappingJob
        job = MappingJob(**job_data)
        db.create_job(job)
        
        print("✅ Created sample mapping job: sample_job_001")
        return True
        
    except Exception as e:
        print(f"⚠️ Error creating sample job: {e}")
        return False


def create_sample_ingestion_job():
    """Create a sample ingestion job for testing"""
    
    from database import get_db_manager
    from ingestion_models import IngestionJobConfig, ConnectorConfig
    
    db = get_db_manager()
    
    # Create ingestion job config
    config = IngestionJobConfig(
        job_id="sample_ingestion_001",
        job_name="Sample FHIR Ingestion Test",
        source_connector=ConnectorConfig(
            type="FHIR",
            config={
                "resource_type": "Patient",
                "source": "sample_data"
            }
        ),
        destination_connector=ConnectorConfig(
            type="MongoDB",
            config={
                "database": "ehr",
                "collection": "fhir_Patient"
            }
        ),
        mapping_job_id="sample_job_001",
        resource_type_override="Patient",
        fhir_store_enabled=True,
        fhir_store_db="ehr",
        fhir_store_mode="per_resource",
        omop_auto_sync=True,
        omop_target_table="PERSON",
        omop_sync_batch_size=50
    )
    
    try:
        # Store the config
        db.store_ingestion_job_config(config)
        print("✅ Created sample ingestion job: sample_ingestion_001")
        return True
        
    except Exception as e:
        print(f"⚠️ Error creating sample ingestion job: {e}")
        return False


def main():
    """Main function to load all sample data"""
    
    print("🚀 Loading sample data for concept normalization testing...")
    
    try:
        # Load FHIR resources
        if not load_sample_fhir_resources():
            return False
        
        # Create mapping job
        if not create_sample_mapping_job():
            return False
        
        # Create ingestion job
        if not create_sample_ingestion_job():
            return False
        
        print("\n✅ Sample data loading complete!")
        print("\n📋 Next steps:")
        print("1. Go to the Data Model screen")
        print("2. Select the 'sample_job_001' job")
        print("3. Click on OMOP tab")
        print("4. Click 'Predict OMOP Table'")
        print("5. Click 'Normalize Concepts' to see concept suggestions")
        print("6. Click 'Review Concepts' to see the HITL interface")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")
        return False


if __name__ == "__main__":
    main()
