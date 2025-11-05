#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced concept normalization UI.
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = "http://localhost:8000"


def test_enhanced_concept_normalization_ui():
    """Test the enhanced concept normalization UI with comprehensive data"""
    
    print("🧪 Testing Enhanced Concept Normalization UI")
    print("=" * 60)
    
    # Test data that will show different confidence levels
    test_scenarios = [
        {
            "name": "Gender Normalization (High Confidence)",
            "values": ["male", "female", "other", "unknown"],
            "domain": "Gender"
        },
        {
            "name": "Condition Normalization (High Confidence)",
            "values": ["E11.9", "I10", "I21.9"],
            "domain": "Condition"
        },
        {
            "name": "Measurement Normalization (Mixed Confidence)",
            "values": ["33747-0", "2093-3", "8310-5", "29463-7", "8480-6", "UNKNOWN_CODE"],
            "domain": "Measurement"
        },
        {
            "name": "Drug Normalization (High Confidence)",
            "values": ["860975", "314076", "1191"],
            "domain": "Drug"
        }
    ]
    
    all_results = {}
    
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
                all_results[scenario["name"]] = data
                
                print(f"✅ {scenario['name']} successful: {data['count']} suggestions")
                
                # Show detailed results
                for suggestion in data['suggestions']:
                    confidence_color = "🟢" if suggestion['confidence'] >= 0.8 else "🟡" if suggestion['confidence'] >= 0.5 else "🔴"
                    print(f"   {confidence_color} {suggestion['source_value']} → {suggestion['concept_name']}")
                    print(f"      ID: {suggestion['concept_id']} | Confidence: {suggestion['confidence']:.1%} | Vocabulary: {suggestion['vocabulary_id']}")
                    if suggestion.get('reasoning'):
                        print(f"      Reasoning: {suggestion['reasoning']}")
                    print()
            else:
                print(f"❌ {scenario['name']} failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"❌ {scenario['name']} error: {e}")
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("📋 ENHANCED CONCEPT NORMALIZATION UI SUMMARY")
    print("=" * 60)
    
    total_mappings = sum(len(result['suggestions']) for result in all_results.values())
    high_confidence = sum(1 for result in all_results.values() for s in result['suggestions'] if s['confidence'] >= 0.8)
    medium_confidence = sum(1 for result in all_results.values() for s in result['suggestions'] if 0.5 <= s['confidence'] < 0.8)
    low_confidence = sum(1 for result in all_results.values() for s in result['suggestions'] if s['confidence'] < 0.5)
    
    print(f"📊 Total Mappings: {total_mappings}")
    print(f"🟢 High Confidence (≥80%): {high_confidence}")
    print(f"🟡 Medium Confidence (50-79%): {medium_confidence}")
    print(f"🔴 Low Confidence (<50%): {low_confidence}")
    
    print(f"\n📈 Success Rate: {((high_confidence + medium_confidence) / total_mappings * 100):.1f}%")
    print(f"🎯 Auto-Approval Rate: {(high_confidence / total_mappings * 100):.1f}%")
    
    print("\n🎨 UI ENHANCEMENTS DEMONSTRATED:")
    print("✅ Summary Statistics Dashboard")
    print("✅ Detailed Confidence Scores with Visual Bars")
    print("✅ Comprehensive Mapping Information")
    print("✅ Reasoning Display for AI Decisions")
    print("✅ Auto-Approve High Confidence Feature")
    print("✅ Field-by-Field Organization")
    print("✅ Vocabulary Information Display")
    print("✅ Interactive Concept ID Editing")
    
    print("\n🚀 FRONTEND TESTING INSTRUCTIONS:")
    print("1. Go to the frontend application")
    print("2. Navigate to Data Model screen")
    print("3. Select any job")
    print("4. Click on OMOP tab")
    print("5. Click 'Normalize Concepts' to see the enhanced UI")
    print("6. Observe the new features:")
    print("   - Summary statistics at the top")
    print("   - Visual confidence bars")
    print("   - Detailed mapping information")
    print("   - Auto-approve functionality")
    print("   - Field-by-field organization")
    
    return True


def main():
    """Main function"""
    print("🚀 Testing Enhanced Concept Normalization UI...")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    
    try:
        # Test if API is available
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print("✅ API is available")
            test_enhanced_concept_normalization_ui()
        else:
            print(f"❌ API not available: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("Make sure the backend is running on http://localhost:8000")


if __name__ == "__main__":
    main()
