#!/usr/bin/env python3
"""
Test script to demonstrate high confidence concept normalization matches.
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = "http://localhost:8000"


def test_high_confidence_matches():
    """Test concept normalization with high confidence matches"""
    
    print("🧪 Testing High Confidence Concept Normalization")
    print("=" * 60)
    
    # Test scenarios with expected high confidence matches
    test_scenarios = [
        {
            "name": "LOINC Lab Codes (High Confidence)",
            "values": ["33747-0", "2093-3", "8310-5", "29463-7", "8480-6"],
            "domain": "Measurement",
            "expected_high_confidence": 5
        },
        {
            "name": "Gender Values (High Confidence)",
            "values": ["male", "female", "other", "unknown"],
            "domain": "Gender",
            "expected_high_confidence": 4
        },
        {
            "name": "ICD-10-CM Diagnosis Codes (High Confidence)",
            "values": ["E11.9", "I10", "I21.9"],
            "domain": "Condition",
            "expected_high_confidence": 3
        },
        {
            "name": "RxNorm Medication Codes (High Confidence)",
            "values": ["860975", "314076", "1191"],
            "domain": "Drug",
            "expected_high_confidence": 3
        },
        {
            "name": "Mixed Confidence Test",
            "values": ["33747-0", "UNKNOWN_CODE", "male", "E11.9", "INVALID_CODE"],
            "domain": "Measurement",  # This will cause some to fail
            "expected_high_confidence": 1  # Only 33747-0 should match
        }
    ]
    
    total_tests = 0
    total_high_confidence = 0
    total_medium_confidence = 0
    total_low_confidence = 0
    
    for scenario in test_scenarios:
        print(f"\n📊 Testing: {scenario['name']}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/omop/concepts/normalize",
                json={
                    "values": scenario["values"],
                    "domain": scenario["domain"],
                    "vocabulary": None
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                suggestions = data['suggestions']
                
                # Count confidence levels
                high_conf = sum(1 for s in suggestions if s['confidence'] >= 0.8)
                medium_conf = sum(1 for s in suggestions if 0.5 <= s['confidence'] < 0.8)
                low_conf = sum(1 for s in suggestions if s['confidence'] < 0.5)
                
                total_tests += len(suggestions)
                total_high_confidence += high_conf
                total_medium_confidence += medium_conf
                total_low_confidence += low_conf
                
                print(f"✅ {scenario['name']} successful: {len(suggestions)} suggestions")
                print(f"   🟢 High Confidence (≥80%): {high_conf}")
                print(f"   🟡 Medium Confidence (50-79%): {medium_conf}")
                print(f"   🔴 Low Confidence (<50%): {low_conf}")
                
                # Show detailed results
                for suggestion in suggestions:
                    confidence_icon = "🟢" if suggestion['confidence'] >= 0.8 else "🟡" if suggestion['confidence'] >= 0.5 else "🔴"
                    print(f"   {confidence_icon} {suggestion['source_value']} → {suggestion['concept_name']}")
                    print(f"      ID: {suggestion['concept_id']} | Confidence: {suggestion['confidence']:.1%} | Vocabulary: {suggestion['vocabulary_id']}")
                
                # Check if we met expectations
                if high_conf >= scenario['expected_high_confidence']:
                    print(f"   ✅ Met expectations: {high_conf}/{scenario['expected_high_confidence']} high confidence matches")
                else:
                    print(f"   ⚠️ Below expectations: {high_conf}/{scenario['expected_high_confidence']} high confidence matches")
                    
            else:
                print(f"❌ {scenario['name']} failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ {scenario['name']} error: {e}")
    
    # Generate comprehensive summary
    print("\n" + "=" * 60)
    print("📋 HIGH CONFIDENCE CONCEPT NORMALIZATION SUMMARY")
    print("=" * 60)
    
    print(f"📊 Total Mappings Tested: {total_tests}")
    print(f"🟢 High Confidence (≥80%): {total_high_confidence} ({(total_high_confidence/total_tests*100):.1f}%)")
    print(f"🟡 Medium Confidence (50-79%): {total_medium_confidence} ({(total_medium_confidence/total_tests*100):.1f}%)")
    print(f"🔴 Low Confidence (<50%): {total_low_confidence} ({(total_low_confidence/total_tests*100):.1f}%)")
    
    success_rate = ((total_high_confidence + total_medium_confidence) / total_tests * 100) if total_tests > 0 else 0
    auto_approval_rate = (total_high_confidence / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    print(f"🎯 Auto-Approval Rate: {auto_approval_rate:.1f}%")
    
    if total_high_confidence > 0:
        print(f"\n✅ SUCCESS: {total_high_confidence} high confidence matches achieved!")
        print("🎉 The enhanced concept normalization UI will now show:")
        print("   - Summary statistics with high confidence counts")
        print("   - Visual confidence bars with exact percentages")
        print("   - Detailed mapping information")
        print("   - Auto-approve functionality for high confidence mappings")
    else:
        print(f"\n❌ ISSUE: No high confidence matches found")
        print("   This suggests a problem with the vocabulary or matching logic")
    
    print("\n🚀 FRONTEND TESTING INSTRUCTIONS:")
    print("1. Go to the frontend application")
    print("2. Navigate to Data Model screen")
    print("3. Select any job")
    print("4. Click on OMOP tab")
    print("5. Click 'Normalize Concepts' to see the enhanced UI")
    print("6. You should now see high confidence matches with 90% confidence scores")
    
    return total_high_confidence > 0


def main():
    """Main function"""
    print("🚀 Testing High Confidence Concept Normalization...")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    
    try:
        # Test if API is available
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print("✅ API is available")
            success = test_high_confidence_matches()
            if success:
                print("\n🎉 High confidence concept normalization is working correctly!")
            else:
                print("\n⚠️ No high confidence matches found - check vocabulary setup")
        else:
            print(f"❌ API not available: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the backend is running on http://localhost:8000")


if __name__ == "__main__":
    main()
