#!/usr/bin/env python3
"""
Load test EHR CSV data and create a mapping job for concept normalization testing.
"""

import sys
import os
import json
import csv
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager


def load_test_csv_data():
    """Load test CSV data and create a mapping job"""
    
    print("🚀 Loading test EHR CSV data for concept normalization testing...")
    
    # Read the CSV file
    csv_file = os.path.join(os.path.dirname(__file__), '..', '..', 'test_ehr_data.csv')
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    # Parse CSV to get schema
    schema = {}
    sample_data = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Infer data types from sample data
        for i, row in enumerate(reader):
            if i < 3:  # Use first 3 rows for type inference
                sample_data.append(row)
                for field, value in row.items():
                    if field not in schema:
                        if value.isdigit():
                            schema[field] = "integer"
                        elif value.replace('.', '').isdigit():
                            schema[field] = "float"
                        elif value.lower() in ['true', 'false']:
                            schema[field] = "boolean"
                        else:
                            schema[field] = "string"
    
    print(f"📊 CSV Schema detected: {len(schema)} fields")
    print(f"📋 Fields: {', '.join(schema.keys())}")
    
    # Create mapping job
    db = get_db_manager()
    
    # Create job data
    job_data = {
        "jobId": "test_ehr_job_001",
        "jobName": "Test EHR Data - Concept Normalization",
        "sourceConnector": {
            "type": "CSV",
            "config": {
                "file_path": "test_ehr_data.csv",
                "delimiter": ",",
                "has_header": True
            }
        },
        "destinationConnector": {
            "type": "FHIR",
            "config": {
                "resource_type": "Patient"
            }
        },
        "sourceSchema": schema,
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
        existing_job = db.get_job("test_ehr_job_001")
        if existing_job:
            print("ℹ️ Test EHR job already exists")
        else:
            # Insert directly into database
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO mappings 
                    (jobId, jobName, sourceConnector, destinationConnector, sourceSchema, 
                     targetSchema, status, finalMappings, userId, createdBy, createdAt, updatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_data["jobId"],
                    job_data["jobName"],
                    json.dumps(job_data["sourceConnector"]),
                    json.dumps(job_data["destinationConnector"]),
                    json.dumps(job_data["sourceSchema"]),
                    json.dumps(job_data["targetSchema"]),
                    job_data["status"],
                    json.dumps(job_data["finalMappings"]),
                    job_data["userId"],
                    job_data["createdBy"],
                    job_data["createdAt"],
                    job_data["updatedAt"]
                ))
            
            print("✅ Created test EHR mapping job: test_ehr_job_001")
        
        # Create ingestion job config
        from ingestion_models import IngestionJobConfig, ConnectorConfig
        
        config = IngestionJobConfig(
            job_id="test_ehr_ingestion_001",
            job_name="Test EHR Ingestion",
            source_connector=ConnectorConfig(
                type="CSV",
                config={
                    "file_path": "test_ehr_data.csv",
                    "delimiter": ",",
                    "has_header": True
                }
            ),
            destination_connector=ConnectorConfig(
                type="MongoDB",
                config={
                    "database": "ehr",
                    "collection": "staging"
                }
            ),
            mapping_job_id="test_ehr_job_001",
            fhir_store_enabled=True,
            fhir_store_db="ehr",
            fhir_store_mode="per_resource",
            omop_auto_sync=True,
            omop_target_table="PERSON",
            omop_sync_batch_size=50
        )
        
        # Store the config
        db.store_ingestion_job_config(config)
        print("✅ Created test EHR ingestion job: test_ehr_ingestion_001")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Error creating test EHR job: {e}")
        return False


def create_sample_fhir_from_csv():
    """Create sample FHIR resources from CSV data for testing"""
    
    print("\n📝 Creating sample FHIR resources from CSV data...")
    
    csv_file = os.path.join(os.path.dirname(__file__), '..', '..', 'test_ehr_data.csv')
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    fhir_resources = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Create Patient resource
            patient = {
                "resourceType": "Patient",
                "id": f"patient-{row['patient_id']}",
                "identifier": [
                    {
                        "system": "MRN",
                        "value": row['mrn']
                    }
                ],
                "name": [
                    {
                        "family": row['last_name'],
                        "given": [row['first_name']]
                    }
                ],
                "gender": row['gender'],
                "birthDate": row['birth_date'],
                "job_id": "test_ehr_job_001"
            }
            fhir_resources.append(patient)
            
            # Create Condition resource if diagnosis exists
            if row['diagnosis_code'] and row['diagnosis_description']:
                condition = {
                    "resourceType": "Condition",
                    "id": f"condition-{row['patient_id']}",
                    "subject": {
                        "reference": f"Patient/patient-{row['patient_id']}"
                    },
                    "code": {
                        "coding": [
                            {
                                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                                "code": row['diagnosis_code'],
                                "display": row['diagnosis_description']
                            }
                        ]
                    },
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active"
                            }
                        ]
                    },
                    "onsetDateTime": row['visit_date'],
                    "job_id": "test_ehr_job_001"
                }
                fhir_resources.append(condition)
            
            # Create Observation resource if lab data exists
            if row['lab_code'] and row['lab_description']:
                observation = {
                    "resourceType": "Observation",
                    "id": f"obs-{row['patient_id']}",
                    "subject": {
                        "reference": f"Patient/patient-{row['patient_id']}"
                    },
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": row['lab_code'],
                                "display": row['lab_description']
                            }
                        ]
                    },
                    "valueQuantity": {
                        "value": float(row['lab_value']) if row['lab_value'] else None,
                        "unit": row['lab_unit']
                    },
                    "effectiveDateTime": row['lab_date'],
                    "job_id": "test_ehr_job_001"
                }
                fhir_resources.append(observation)
            
            # Create MedicationRequest if medication exists
            if row['medication_code'] and row['medication_name']:
                medication = {
                    "resourceType": "MedicationRequest",
                    "id": f"med-{row['patient_id']}",
                    "subject": {
                        "reference": f"Patient/patient-{row['patient_id']}"
                    },
                    "medicationCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": row['medication_code'],
                                "display": row['medication_name']
                            }
                        ]
                    },
                    "authoredOn": row['prescription_date'],
                    "dosageInstruction": [
                        {
                            "doseQuantity": {
                                "value": float(row['dosage']) if row['dosage'] else None,
                                "unit": row['unit']
                            }
                        }
                    ],
                    "job_id": "test_ehr_job_001"
                }
                fhir_resources.append(medication)
    
    # Save FHIR resources to file
    fhir_file = os.path.join(os.path.dirname(__file__), '..', '..', 'test_data', 'test_ehr_fhir_resources.json')
    os.makedirs(os.path.dirname(fhir_file), exist_ok=True)
    
    with open(fhir_file, 'w') as f:
        json.dump(fhir_resources, f, indent=2)
    
    print(f"✅ Created {len(fhir_resources)} FHIR resources from CSV data")
    print(f"📁 Saved to: {fhir_file}")
    
    return True


def main():
    """Main function"""
    print("🚀 Setting up test EHR data for concept normalization...")
    
    try:
        # Load CSV data and create mapping job
        if not load_test_csv_data():
            return False
        
        # Create FHIR resources from CSV
        if not create_sample_fhir_from_csv():
            return False
        
        print("\n✅ Test EHR data setup complete!")
        print("\n📋 Test Data Summary:")
        print("  - CSV File: test_ehr_data.csv (10 patients)")
        print("  - Mapping Job: test_ehr_job_001")
        print("  - Ingestion Job: test_ehr_ingestion_001")
        print("  - FHIR Resources: test_data/test_ehr_fhir_resources.json")
        
        print("\n🎯 Concept Normalization Test Data:")
        print("  - Gender values: male, female")
        print("  - Diagnosis codes: E11.9, I10, I21.9 (ICD-10-CM)")
        print("  - Lab codes: 33747-0, 2093-3, 8310-5, 29463-7, 8480-6 (LOINC)")
        print("  - Medication codes: 860975, 314076, 1191 (RxNorm)")
        
        print("\n📋 Next Steps:")
        print("1. Go to the frontend application")
        print("2. Navigate to Data Model screen")
        print("3. Select 'test_ehr_job_001' job")
        print("4. Click on OMOP tab")
        print("5. Click 'Predict OMOP Table'")
        print("6. Click 'Normalize Concepts' to see concept suggestions")
        print("7. Click 'Review Concepts' to see the HITL interface")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        return False


if __name__ == "__main__":
    main()
