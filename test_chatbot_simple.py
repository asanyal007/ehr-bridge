#!/usr/bin/env python3
"""
Simple test to check chatbot error
"""
import httpx
import json

API_BASE_URL = "http://localhost:8000"

def test_chatbot():
    try:
        # Get auth token
        print("Getting auth token...")
        with httpx.Client(timeout=10.0) as client:
            token_resp = client.post(f"{API_BASE_URL}/api/v1/auth/demo-token")
            token_resp.raise_for_status()
            token = token_resp.json().get('token')
            print(f"[OK] Got token: {token[:20]}...")
        
        # Test chatbot query
        print("\nTesting chatbot query: 'How many patients do we have?'")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        payload = {
            "question": "How many patients do we have?"
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{API_BASE_URL}/api/v1/chat/query",
                json=payload,
                headers=headers
            )
            
            print(f"\n[HTTP STATUS]: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[ERROR] HTTP Error: {response.status_code}")
                print(f"[ERROR] Response: {response.text}")
                return
            
            result = response.json()
            
            print(f"\n[RESULT]:")
            print(f"Answer: {result.get('answer', 'N/A')}")
            print(f"Results Count: {result.get('results_count', 0)}")
            print(f"Query Used: {json.dumps(result.get('query_used', {}), indent=2)}")
            
            if 'error' in result:
                print(f"\n[ERROR]: {result.get('error')}")
            if 'metadata' in result:
                print(f"\n[METADATA]: {json.dumps(result.get('metadata', {}), indent=2)}")
                if 'error' in result['metadata']:
                    print(f"\n[METADATA ERROR]: {result['metadata'].get('error')}")
                    if 'error_trace' in result['metadata']:
                        print(f"\n[TRACEBACK]:\n{result['metadata']['error_trace']}")
            
            # Check backend logs suggestion
            if 'error' in result or (result.get('results_count', 0) == 0 and 'No' in result.get('answer', '')):
                print(f"\n[DEBUGGING INFO]:")
                print(f"  - Check backend console logs for detailed error messages")
                print(f"  - Verify MongoDB is running on localhost:27017")
                print(f"  - Verify staging collection has data with resourceType='Patient'")
            
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatbot()

