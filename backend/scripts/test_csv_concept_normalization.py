#!/usr/bin/env python3
"""
Test concept normalization with the CSV data.
"""

import sys
import os
import json
import csv
import requests
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = "http://localhost:8000"


def extract_test_values_from_csv():
    """Extract test values from the CSV file for concept normalization"""
    
    csv_file = os.path.join(os.path.dirname(__file__), '..', '..', 'test_ehr_data.csv')
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return None
    
    # Extract unique values for each domain
    gender_values = set()
    diagnosis_codes = set()
    lab_codes = set()
    medication_codes = set()
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Gender values
            if row['gender']:
                gender_values.add(row['gender'])
            
            # Diagnosis codes
            if row['diagnosis_code']:
                diagnosis_codes.add(row['diagnosis_code'])
            
            # Lab codes
            if row['lab_code']:
                lab_codes.add(row['lab_code'])
            
            # Medication codes
            if row['medication_code']:
                medication_codes.add(row['medication_code'])
    
    return {
        'gender': list(gender_values),
        'diagnosis': list(diagnosis_codes),
        'lab': list(lab_codes),
        'medication': list(medication_codes)
    }


def test_concept_normalization_with_csv():
    """Test concept normalization using values from the CSV file"""
    
    print("🧪 Testing Concept Normalization with CSV Data")
    print("=" * 60)
    
    # Extract test values from CSV
    test_values = extract_test_values_from_csv()
    
    if not test_values:
        print("❌ Could not extract test values from CSV")
        return False
    
    print(f"📊 Extracted test values from CSV:")
    print(f"  - Gender: {test_values['gender']}")
    print(f"  - Diagnosis codes: {test_values['diagnosis']}")
    print(f"  - Lab codes: {test_values['lab']}")
    print(f"  - Medication codes: {test_values['medication']}")
    
    # Test 1: Gender normalization
    print("\n1️⃣ Testing Gender Concept Normalization")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
            json={
                "values": test_values['gender'],
                "domain": "Gender",
                "vocabulary": None
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Gender normalization successful: {data['count']} suggestions")
            for suggestion in data['suggestions']:
                print(f"   {suggestion['source_value']} → {suggestion['concept_name']} (ID: {suggestion['concept_id']}, Confidence: {suggestion['confidence']:.2f})")
        else:
            print(f"❌ Gender normalization failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Gender normalization error: {e}")
    
    # Test 2: Diagnosis normalization
    print("\n2️⃣ Testing Diagnosis Concept Normalization")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
            json={
                "values": test_values['diagnosis'],
                "domain": "Condition",
                "vocabulary": None
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Diagnosis normalization successful: {data['count']} suggestions")
            for suggestion in data['suggestions']:
                print(f"   {suggestion['source_value']} → {suggestion['concept_name']} (ID: {suggestion['concept_id']}, Confidence: {suggestion['confidence']:.2f})")
        else:
            print(f"❌ Diagnosis normalization failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Diagnosis normalization error: {e}")
    
    # Test 3: Lab normalization
    print("\n3️⃣ Testing Lab Concept Normalization")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
            json={
                "values": test_values['lab'],
                "domain": "Measurement",
                "vocabulary": None
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Lab normalization successful: {data['count']} suggestions")
            for suggestion in data['suggestions']:
                print(f"   {suggestion['source_value']} → {suggestion['concept_name']} (ID: {suggestion['concept_id']}, Confidence: {suggestion['confidence']:.2f})")
        else:
            print(f"❌ Lab normalization failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Lab normalization error: {e}")
    
    # Test 4: Medication normalization
    print("\n4️⃣ Testing Medication Concept Normalization")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
            json={
                "values": test_values['medication'],
                "domain": "Drug",
                "vocabulary": None
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Medication normalization successful: {data['count']} suggestions")
            for suggestion in data['suggestions']:
                print(f"   {suggestion['source_value']} → {suggestion['concept_name']} (ID: {suggestion['concept_id']}, Confidence: {suggestion['confidence']:.2f})")
        else:
            print(f"❌ Medication normalization failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Medication normalization error: {e}")
    
    # Test 5: Mixed domain normalization
    print("\n5️⃣ Testing Mixed Domain Normalization")
    print("-" * 50)
    
    mixed_values = test_values['diagnosis'] + test_values['lab'] + test_values['medication']
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
            json={
                "values": mixed_values,
                "domain": "Mixed",
                "vocabulary": None
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Mixed domain normalization successful: {data['count']} suggestions")
            for suggestion in data['suggestions']:
                print(f"   {suggestion['source_value']} → {suggestion['concept_name']} (ID: {suggestion['concept_id']}, Confidence: {suggestion['confidence']:.2f})")
        else:
            print(f"❌ Mixed domain normalization failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Mixed domain normalization error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 CSV Concept Normalization Testing Complete!")
    
    return True


def main():
    """Main function"""
    print("🚀 Testing Concept Normalization with CSV Data...")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    
    try:
        # Test if API is available
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print("✅ API is available")
            test_concept_normalization_with_csv()
        else:
            print(f"❌ API not available: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the backend is running on http://localhost:8000")


if __name__ == "__main__":
    main()
