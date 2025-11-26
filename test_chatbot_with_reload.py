#!/usr/bin/env python3
"""
Test chatbot with service reload
"""
import httpx
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_chatbot_with_reload():
    try:
        # Get auth token
        print("Getting auth token...")
        with httpx.Client(timeout=10.0) as client:
            token_resp = client.post(f"{API_BASE_URL}/api/v1/auth/demo-token")
            token_resp.raise_for_status()
            token = token_resp.json().get('token')
            print(f"[OK] Got token")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        # Step 1: Reload chatbot service
        print("\n[STEP 1] Reloading chatbot service...")
        try:
            with httpx.Client(timeout=10.0) as client:
                reload_resp = client.post(
                    f"{API_BASE_URL}/api/v1/chat/reload",
                    headers=headers
                )
                if reload_resp.status_code == 200:
                    print(f"[OK] Chatbot service reloaded")
                else:
                    print(f"[WARN] Reload endpoint returned: {reload_resp.status_code}")
                    print(f"[WARN] Response: {reload_resp.text}")
        except Exception as e:
            print(f"[WARN] Could not reload service (endpoint may not exist yet): {e}")
            print(f"[INFO] You may need to restart the backend server instead")
        
        # Wait a moment for reload
        time.sleep(1)
        
        # Step 2: Test chatbot query
        print("\n[STEP 2] Testing chatbot query: 'How many patients do we have?'")
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
                meta = result.get('metadata', {})
                if 'error' in meta:
                    print(f"\n[METADATA ERROR]: {meta.get('error')}")
            
            # Check if it worked
            if result.get('results_count', 0) > 0 or '173' in result.get('answer', ''):
                print(f"\n[SUCCESS] Chatbot is working correctly!")
            else:
                print(f"\n[ISSUE] Chatbot returned 0 results")
                print(f"[SOLUTION] Restart the backend server to load the updated code")
            
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatbot_with_reload()

