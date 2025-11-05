#!/usr/bin/env python3
"""
Seed basic OMOP vocabulary data for testing concept normalization.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager


def seed_basic_omop_vocab():
    """Seed basic OMOP vocabulary concepts for testing"""
    
    db = get_db_manager()
    
    # Basic concepts for testing
    concepts = [
        # Gender concepts
        {"concept_id": 8507, "concept_name": "MALE", "vocabulary_id": "Gender", "domain_id": "Gender", "standard_concept": "S", "concept_code": "M"},
        {"concept_id": 8532, "concept_name": "FEMALE", "vocabulary_id": "Gender", "domain_id": "Gender", "standard_concept": "S", "concept_code": "F"},
        {"concept_id": 8521, "concept_name": "OTHER", "vocabulary_id": "Gender", "domain_id": "Gender", "standard_concept": "S", "concept_code": "O"},
        {"concept_id": 0, "concept_name": "UNKNOWN", "vocabulary_id": "Gender", "domain_id": "Gender", "standard_concept": "S", "concept_code": "U"},
        
        # Condition concepts (ICD-10 based)
        {"concept_id": 201820, "concept_name": "Type 2 diabetes mellitus without complications", "vocabulary_id": "ICD10CM", "domain_id": "Condition", "standard_concept": "S", "concept_code": "E11.9"},
        {"concept_id": 320128, "concept_name": "Essential hypertension", "vocabulary_id": "ICD10CM", "domain_id": "Condition", "standard_concept": "S", "concept_code": "I10"},
        {"concept_id": 201254, "concept_name": "Acute myocardial infarction", "vocabulary_id": "ICD10CM", "domain_id": "Condition", "standard_concept": "S", "concept_code": "I21.9"},
        
        # Measurement concepts (LOINC based)
        {"concept_id": 3004501, "concept_name": "Glucose [Mass/volume] in Blood", "vocabulary_id": "LOINC", "domain_id": "Measurement", "standard_concept": "S", "concept_code": "33747-0"},
        {"concept_id": 3004249, "concept_name": "Cholesterol, Total", "vocabulary_id": "LOINC", "domain_id": "Measurement", "standard_concept": "S", "concept_code": "2093-3"},
        {"concept_id": 3020891, "concept_name": "Body temperature", "vocabulary_id": "LOINC", "domain_id": "Measurement", "standard_concept": "S", "concept_code": "8310-5"},
        {"concept_id": 3025315, "concept_name": "Body weight", "vocabulary_id": "LOINC", "domain_id": "Measurement", "standard_concept": "S", "concept_code": "29463-7"},
        {"concept_id": 3004249, "concept_name": "Systolic blood pressure", "vocabulary_id": "LOINC", "domain_id": "Measurement", "standard_concept": "S", "concept_code": "8480-6"},
        
        # Drug concepts (RxNorm based)
        {"concept_id": 1503297, "concept_name": "Metformin hydrochloride 500 MG Oral Tablet", "vocabulary_id": "RxNorm", "domain_id": "Drug", "standard_concept": "S", "concept_code": "860975"},
        {"concept_id": 1308216, "concept_name": "Lisinopril 10 MG Oral Tablet", "vocabulary_id": "RxNorm", "domain_id": "Drug", "standard_concept": "S", "concept_code": "314076"},
        {"concept_id": 1503320, "concept_name": "Aspirin 81 MG Oral Tablet", "vocabulary_id": "RxNorm", "domain_id": "Drug", "standard_concept": "S", "concept_code": "1191"},
    ]
    
    print(f"📊 Seeding {len(concepts)} OMOP concepts...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create concept table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concept (
                    concept_id INTEGER PRIMARY KEY,
                    concept_name TEXT NOT NULL,
                    vocabulary_id TEXT NOT NULL,
                    domain_id TEXT NOT NULL,
                    standard_concept TEXT,
                    concept_code TEXT
                )
            """)
            
            # Insert concepts
            for concept in concepts:
                cursor.execute("""
                    INSERT OR REPLACE INTO concept 
                    (concept_id, concept_name, vocabulary_id, domain_id, standard_concept, concept_code)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    concept["concept_id"],
                    concept["concept_name"],
                    concept["vocabulary_id"],
                    concept["domain_id"],
                    concept["standard_concept"],
                    concept["concept_code"]
                ))
            
            print(f"✅ Successfully seeded {len(concepts)} OMOP concepts")
            
            # Print summary by domain
            domains = {}
            for concept in concepts:
                domain = concept["domain_id"]
                if domain not in domains:
                    domains[domain] = 0
                domains[domain] += 1
            
            print("\n📋 Concept Summary by Domain:")
            for domain, count in domains.items():
                print(f"  - {domain}: {count} concepts")
            
            return True
            
    except Exception as e:
        print(f"❌ Error seeding OMOP vocabulary: {e}")
        return False


def main():
    """Main function"""
    print("🚀 Seeding OMOP vocabulary for concept normalization testing...")
    
    if seed_basic_omop_vocab():
        print("\n✅ OMOP vocabulary seeding complete!")
        print("\n📋 Now you can test concept normalization:")
        print("1. Go to the Data Model screen")
        print("2. Select any job")
        print("3. Click on OMOP tab")
        print("4. Click 'Normalize Concepts' to see concept suggestions")
        print("5. Click 'Review Concepts' to see the HITL interface")
    else:
        print("❌ Failed to seed OMOP vocabulary")


if __name__ == "__main__":
    main()
