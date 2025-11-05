#!/usr/bin/env python3
"""
Add missing LOINC codes for vital signs measurements.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager


def add_vital_signs_loinc():
    """Add missing LOINC codes for vital signs"""

    db = get_db_manager()

    # Missing LOINC codes for vital signs
    vital_signs_codes = [
        {
            "concept_id": 3000005,
            "concept_name": "Diastolic blood pressure",
            "vocabulary_id": "LOINC",
            "domain_id": "Measurement",
            "standard_concept": "S",
            "concept_code": "8462-4"
        },
        {
            "concept_id": 3000006,
            "concept_name": "Heart rate",
            "vocabulary_id": "LOINC",
            "domain_id": "Measurement",
            "standard_concept": "S",
            "concept_code": "8867-4"
        },
        {
            "concept_id": 3000007,
            "concept_name": "Body height",
            "vocabulary_id": "LOINC",
            "domain_id": "Measurement",
            "standard_concept": "S",
            "concept_code": "8302-2"
        }
    ]

    print("📊 Adding missing vital signs LOINC codes...")

    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Insert missing LOINC concepts
            for concept in vital_signs_codes:
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

            print(f"\n✅ Successfully added {len(vital_signs_codes)} vital signs LOINC codes")

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
        print(f"❌ Error adding vital signs codes: {e}")
        return False


def main():
    """Main function"""
    print("🚀 Adding missing vital signs LOINC codes...")

    if add_vital_signs_loinc():
        print("\n✅ Vital signs codes added successfully!")
    else:
        print("❌ Failed to add vital signs codes")


if __name__ == "__main__":
    main()
