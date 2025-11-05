#!/usr/bin/env python3
"""
Add missing LOINC codes from the CSV data to the OMOP vocabulary.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager


def add_missing_loinc_codes():
    """Add missing LOINC codes from CSV data to OMOP vocabulary"""
    
    db = get_db_manager()
    
    # LOINC codes from the CSV that are missing
    missing_loinc_codes = [
        {
            "concept_id": 3000001,
            "concept_name": "Sodium [Moles/volume] in Serum or Plasma",
            "vocabulary_id": "LOINC",
            "domain_id": "Measurement",
            "standard_concept": "S",
            "concept_code": "2951-2"
        },
        {
            "concept_id": 3000002,
            "concept_name": "Glucose [Mass/volume] in Serum or Plasma",
            "vocabulary_id": "LOINC",
            "domain_id": "Measurement",
            "standard_concept": "S",
            "concept_code": "2345-7"
        },
        {
            "concept_id": 3000003,
            "concept_name": "Hemoglobin [Mass/volume] in Blood",
            "vocabulary_id": "LOINC",
            "domain_id": "Measurement",
            "standard_concept": "S",
            "concept_code": "718-7"
        }
    ]
    
    print(f"📊 Adding {len(missing_loinc_codes)} missing LOINC codes...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert missing LOINC concepts
            for concept in missing_loinc_codes:
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
                
                print(f"✅ Added: {concept['concept_code']} - {concept['concept_name']}")
            
            print(f"\n✅ Successfully added {len(missing_loinc_codes)} LOINC concepts")
            
            # Verify the additions
            cursor.execute("""
                SELECT concept_id, concept_name, concept_code, vocabulary_id 
                FROM concept 
                WHERE vocabulary_id = 'LOINC' 
                ORDER BY concept_id
            """)
            all_loinc = cursor.fetchall()
            
            print(f"\n📋 All LOINC concepts now ({len(all_loinc)} total):")
            for concept in all_loinc:
                print(f"  {concept[2]} - {concept[1]} (ID: {concept[0]})")
            
            return True
            
    except Exception as e:
        print(f"❌ Error adding LOINC codes: {e}")
        return False


def main():
    """Main function"""
    print("🚀 Adding missing LOINC codes for high confidence matches...")
    
    if add_missing_loinc_codes():
        print("\n✅ LOINC codes added successfully!")
        print("\n🧪 Now test the concept normalization:")
        print("curl -X POST http://localhost:8000/api/v1/omop/concepts/normalize \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{\"values\": [\"2951-2\", \"2345-7\", \"718-7\"], \"domain\": \"Measurement\"}'")
    else:
        print("❌ Failed to add LOINC codes")


if __name__ == "__main__":
    main()
