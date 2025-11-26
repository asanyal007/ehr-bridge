#!/usr/bin/env python3
"""
Direct test of chatbot service (bypassing API)
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fhir_chatbot_service import FHIRChatbotService

def test_chatbot_direct():
    print("Initializing chatbot service...")
    try:
        chatbot = FHIRChatbotService()
        
        print(f"\n[INFO] MongoDB client: {chatbot.mongo_client}")
        print(f"[INFO] MongoDB database: {chatbot.mongo_db}")
        
        if chatbot.mongo_client:
            # Test direct query
            db = chatbot.mongo_client[chatbot.mongo_db]
            print(f"\n[INFO] Testing direct MongoDB query...")
            
            if 'staging' in db.list_collection_names():
                collection = db['staging']
                staging_filter = {'resourceType': 'Patient'}
                count = collection.count_documents(staging_filter)
                print(f"[RESULT] Direct MongoDB query: {count} Patient records in staging")
            else:
                print(f"[ERROR] staging collection not found")
                print(f"[INFO] Available collections: {db.list_collection_names()}")
        
        print("\n[INFO] Testing chatbot query...")
        result = chatbot.chat("How many patients do we have?")
        
        print(f"\n[RESULT]:")
        print(f"Answer: {result.get('answer', 'N/A')}")
        print(f"Results Count: {result.get('results_count', 0)}")
        print(f"Query Used: {result.get('query_used', {})}")
        
        if 'error' in result:
            print(f"\n[ERROR]: {result.get('error')}")
        if 'metadata' in result and 'error' in result['metadata']:
            print(f"\n[METADATA ERROR]: {result['metadata'].get('error')}")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatbot_direct()

