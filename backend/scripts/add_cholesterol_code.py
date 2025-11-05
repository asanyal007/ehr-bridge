#!/usr/bin/env python3
"""
Add the missing Cholesterol Total LOINC code.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_manager


def add_cholesterol_code():
    """Add the missing Cholesterol Total LOINC code"""
    
    db = get_db_manager()
    
    # Add the missing Cholesterol Total code
    cholesterol_concept = {
        "concept_id": 3000004,
        "concept_name": "Cholesterol, Total",
        "vocabulary_id": "LOINC",
        "domain_id": "Measurement",
        "standard_concept": "S",
        "concept_code": "2093-3"
    }
    
    print("📊 Adding missing Cholesterol Total LOINC code...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert the cholesterol concept
            cursor.execute("""
                INSERT OR REPLACE INTO concept 
                (concept_id, concept_name, vocabulary_id, domain_id, standard_concept, concept_code)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cholesterol_concept["concept_id"],
                cholesterol_concept["concept_name"],
                cholesterol_concept["vocabulary_id"],
                cholesterol_concept["domain_id"],
                cholesterol_concept["standard_concept"],
                cholesterol_concept["concept_code"]
            ))
            
            print(f"✅ Added: {cholesterol_concept['concept_code']} - {cholesterol_concept['concept_name']}")
            
            # Verify the addition
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
        print(f"❌ Error adding cholesterol code: {e}")
        return False


def main():
    """Main function"""
    print("🚀 Adding missing Cholesterol Total LOINC code...")
    
    if add_cholesterol_code():
        print("\n✅ Cholesterol code added successfully!")
        print("\n🧪 Now test all LOINC codes from CSV:")
        print("curl -X POST http://localhost:8000/api/v1/omop/concepts/normalize \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{\"values\": [\"33747-0\", \"2093-3\", \"8310-5\", \"29463-7\", \"8480-6\"], \"domain\": \"Measurement\"}'")
    else:
        print("❌ Failed to add cholesterol code")


if __name__ == "__main__":
    main()
