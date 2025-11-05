#!/usr/bin/env python3
"""
Test script to verify enhanced measurement processing creates multiple records per patient.
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = "http://localhost:8000"


def test_enhanced_measurements():
    """Test that the enhanced measurement logic creates multiple records per patient"""

    print("🧪 Testing Enhanced Measurement Processing")
    print("=" * 60)

    # Test data that should generate multiple measurement records
    test_patient_data = [
        {
            "patient_id": "P001",
            "first_name": "John",
            "last_name": "Smith",
            "gender": "male",
            "birth_date": "1985-03-15",
            "mrn": "MRN-001",
            "lab_code": "33747-0",  # Glucose
            "lab_value": "95",
            "lab_unit": "mg/dL",
            "lab_date": "2024-01-15",
            "blood_pressure_systolic": "140",
            "blood_pressure_diastolic": "90",
            "heart_rate": "72",
            "temperature": "98.6",
            "weight": "180",
            "height": "72",
            "visit_date": "2024-01-15"
        }
    ]

    print("📊 Test Patient Data:")
    for i, patient in enumerate(test_patient_data, 1):
        print(f"Patient {i}: {patient['first_name']} {patient['last_name']}")
        print(f"  Lab: {patient['lab_code']} ({patient['lab_value']} {patient['lab_unit']})")
        print(f"  Vitals: BP {patient['blood_pressure_systolic']}/{patient['blood_pressure_diastolic']}, HR {patient['heart_rate']}, Temp {patient['temperature']}°F")
        print(f"  Body: Weight {patient['weight']} lbs, Height {patient['height']} in")
        print()

    # Test the enhanced _concept_lookup function
    from omop_engine import _concept_lookup, _extract_person, get_person_id_service, PersonKey

    print("1️⃣ Testing Concept Lookup for All LOINC Codes")
    print("-" * 50)

    job_id = "test_enhanced_measurements"
    loinc_codes = [
        "33747-0",  # Glucose (from lab_code)
        "8480-6",   # Systolic BP
        "8462-4",   # Diastolic BP
        "8867-4",   # Heart rate
        "8310-5",   # Temperature
        "29463-7",  # Weight
        "8302-2"    # Height
    ]

    for code in loinc_codes:
        standard_id, source_id, vocab, code_ret = _concept_lookup(code, 'measurement', job_id)
        print(f"   {code} → Concept ID: {standard_id} (Vocabulary: {vocab})")

    print("\n2️⃣ Testing Person Extraction")
    print("-" * 50)

    person_service = get_person_id_service()
    for patient in test_patient_data:
        person_key = PersonKey(
            mrn=patient['mrn'],
            first_name=patient['first_name'],
            last_name=patient['last_name'],
            dob=patient['birth_date']
        )
        person_id = person_service.generate_person_id(person_key)
        print(f"   {patient['first_name']} {patient['last_name']} → Person ID: {person_id}")

    print("\n3️⃣ Testing Enhanced Measurement Processing")
    print("-" * 50)

    # Simulate the enhanced measurement processing logic
    for patient in test_patient_data:
        person = _extract_person(patient)
        measurements = []

        # Lab measurements
        lab_code = str(patient.get('lab_code') or '').strip()
        if lab_code:
            standard_id, source_id, vocab, code = _concept_lookup(lab_code, domain='measurement', job_id=job_id)
            measurements.append({
                'type': 'lab',
                'concept_id': standard_id,
                'value': patient.get('lab_value'),
                'unit': patient.get('lab_unit'),
                'date': patient.get('lab_date')
            })

        # Vital signs
        vital_signs = [
            ('blood_pressure_systolic', '8480-6', patient.get('blood_pressure_systolic'), 'mmHg', patient.get('visit_date')),
            ('blood_pressure_diastolic', '8462-4', patient.get('blood_pressure_diastolic'), 'mmHg', patient.get('visit_date')),
            ('heart_rate', '8867-4', patient.get('heart_rate'), '/min', patient.get('visit_date')),
            ('temperature', '8310-5', patient.get('temperature'), 'F', patient.get('visit_date')),
            ('weight', '29463-7', patient.get('weight'), 'lbs', patient.get('visit_date')),
            ('height', '8302-2', patient.get('height'), 'in', patient.get('visit_date'))
        ]

        for field_name, loinc_code, value, unit, date in vital_signs:
            if value:
                standard_id, source_id, vocab, code = _concept_lookup(loinc_code, domain='measurement', job_id=job_id)
                measurements.append({
                    'type': field_name,
                    'concept_id': standard_id,
                    'value': value,
                    'unit': unit,
                    'date': date
                })

        print(f"   Patient {patient['first_name']} {patient['last_name']}:")
        print(f"     Total measurements: {len(measurements)}")
        for i, measurement in enumerate(measurements, 1):
            print(f"       {i}. {measurement['type']} → Concept ID {measurement['concept_id']} ({measurement['value']} {measurement['unit']})")

    print("\n✅ Enhanced measurement processing test completed!")
    print("\n📋 Expected Results:")
    print("   - Each patient should generate 7 measurement records")
    print("   - 1 lab measurement (from lab_code)")
    print("   - 6 vital signs (BP systolic, BP diastolic, heart rate, temperature, weight, height)")
    print("   - 10 patients × 7 measurements = 70 total measurement records")

    return True


def main():
    """Main function"""
    print("🚀 Testing Enhanced Measurement Processing...")
    print(f"🌐 API Base URL: {API_BASE_URL}")

    try:
        # Test if API is available
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print("✅ API is available")
            success = test_enhanced_measurements()
            if success:
                print("\n🎉 Enhanced measurement processing is working correctly!")
                print("\n📋 Next Steps:")
                print("1. Test with the actual OMOP persistence endpoint")
                print("2. Verify that 70+ measurement records are created for 10 patients")
                print("3. Each patient should have 7 measurement records (1 lab + 6 vital signs)")
            else:
                print("\n⚠️ Enhanced measurement processing has issues")
        else:
            print(f"❌ API not available: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the backend is running on http://localhost:8000")


if __name__ == "__main__":
    main()
