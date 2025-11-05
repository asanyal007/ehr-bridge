#!/usr/bin/env python3
"""
Test script to demonstrate concept normalization workflow.
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = "http://localhost:8000"


def test_concept_normalization():
    """Test the concept normalization workflow"""
    
    print("🧪 Testing Concept Normalization Workflow")
    print("=" * 50)
    
    # Test 1: Gender normalization
    print("\n1️⃣ Testing Gender Concept Normalization")
    print("-" * 40)
    
    gender_payload = {
        "values": ["male", "female", "other", "unknown"],
        "domain": "Gender",
        "vocabulary": None
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
            json=gender_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Gender normalization successful: {data['count']} suggestions")
            for suggestion in data['suggestions']:
                print(f"   {suggestion['source_value']} → {suggestion['concept_name']} (ID: {suggestion['concept_id']}, Confidence: {suggestion['confidence']:.2f})")
        else:
            print(f"❌ Gender normalization failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Gender normalization error: {e}")
    
    # Test 2: Condition normalization
    print("\n2️⃣ Testing Condition Concept Normalization")
    print("-" * 40)
    
    condition_payload = {
        "values": ["E11.9", "I10", "I21.9", "Z00.00"],
        "domain": "Condition",
        "vocabulary": None
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
            json=condition_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Condition normalization successful: {data['count']} suggestions")
            for suggestion in data['suggestions']:
                print(f"   {suggestion['source_value']} → {suggestion['concept_name']} (ID: {suggestion['concept_id']}, Confidence: {suggestion['confidence']:.2f})")
        else:
            print(f"❌ Condition normalization failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Condition normalization error: {e}")
    
    # Test 3: Measurement normalization
    print("\n3️⃣ Testing Measurement Concept Normalization")
    print("-" * 40)
    
    measurement_payload = {
        "values": ["33747-0", "2093-3", "8310-5", "29463-7"],
        "domain": "Measurement",
        "vocabulary": None
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
            json=measurement_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Measurement normalization successful: {data['count']} suggestions")
            for suggestion in data['suggestions']:
                print(f"   {suggestion['source_value']} → {suggestion['concept_name']} (ID: {suggestion['concept_id']}, Confidence: {suggestion['confidence']:.2f})")
        else:
            print(f"❌ Measurement normalization failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Measurement normalization error: {e}")
    
    # Test 4: Drug normalization
    print("\n4️⃣ Testing Drug Concept Normalization")
    print("-" * 40)
    
    drug_payload = {
        "values": ["860975", "314076", "1191"],
        "domain": "Drug",
        "vocabulary": None
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
            json=drug_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Drug normalization successful: {data['count']} suggestions")
            for suggestion in data['suggestions']:
                print(f"   {suggestion['source_value']} → {suggestion['concept_name']} (ID: {suggestion['concept_id']}, Confidence: {suggestion['confidence']:.2f})")
        else:
            print(f"❌ Drug normalization failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Drug normalization error: {e}")
    
    # Test 5: Concept validation
    print("\n5️⃣ Testing Concept Validation")
    print("-" * 40)
    
    validation_payload = {
        "job_id": "test_job_001",
        "auto_approve_threshold": 0.90
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/omop/concepts/validate",
            json=validation_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Concept validation successful:")
            print(f"   Auto-approved: {data['auto_approved']}")
            print(f"   Review required: {data['review_required']}")
            print(f"   Rejected: {data['rejected']}")
            print(f"   Review queue items: {len(data['review_queue'])}")
        else:
            print(f"❌ Concept validation failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Concept validation error: {e}")
    
    # Test 6: Review queue
    print("\n6️⃣ Testing Review Queue")
    print("-" * 40)
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/omop/concepts/review-queue/test_job_001?status=pending",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Review queue retrieval successful:")
            print(f"   Job ID: {data['job_id']}")
            print(f"   Status: {data['status']}")
            print(f"   Items: {data['count']}")
        else:
            print(f"❌ Review queue retrieval failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Review queue error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Concept Normalization Testing Complete!")
    print("\n📋 Next Steps:")
    print("1. Go to the frontend application")
    print("2. Navigate to Data Model screen")
    print("3. Select any job")
    print("4. Click on OMOP tab")
    print("5. Click 'Normalize Concepts' to see the UI in action")
    print("6. Click 'Review Concepts' to see the HITL interface")


def main():
    """Main function"""
    print("🚀 Starting Concept Normalization Tests...")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    
    try:
        # Test if API is available
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print("✅ API is available")
            test_concept_normalization()
        else:
            print(f"❌ API not available: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the backend is running on http://localhost:8000")


if __name__ == "__main__":
    main()
