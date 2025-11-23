"""
Test script for Local LLM Integration
Tests both local LLM connection and chatbot functionality
"""
import os
import sys
import requests
import json

# Test Configuration
BACKEND_URL = "http://localhost:8000"
LOCAL_LLM_URL = "http://127.0.0.1:1234"


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def test_local_llm_server():
    """Test if local LLM server is running"""
    print_header("TEST 1: Local LLM Server Connection")
    
    try:
        response = requests.get(f"{LOCAL_LLM_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"[OK] Local LLM server is running at {LOCAL_LLM_URL}")
            print(f"Available models: {len(models.get('data', []))}")
            for model in models.get('data', []):
                print(f"  - {model.get('id', 'unknown')}")
            return True
        else:
            print(f"[FAIL] Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Cannot connect to {LOCAL_LLM_URL}")
        print("  Make sure your local LLM server is running (e.g., LM Studio)")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_backend_connection():
    """Test if backend is running"""
    print_header("TEST 2: Backend Server Connection")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print(f"[OK] Backend is running at {BACKEND_URL}")
            return True
        else:
            print(f"[FAIL] Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Cannot connect to {BACKEND_URL}")
        print("  Make sure the backend is running")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_get_current_provider():
    """Test getting current LLM provider"""
    print_header("TEST 3: Get Current LLM Provider")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chat/llm/provider")
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Current provider: {data.get('provider')}")
            if data.get('provider') == 'local_llm':
                print(f"  Local LLM URL: {data.get('local_llm_url')}")
                print(f"  Model: {data.get('model_name')}")
                print(f"  Available: {data.get('available')}")
            return True, data
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False, None


def test_switch_to_local_llm():
    """Test switching to local LLM provider"""
    print_header("TEST 4: Switch to Local LLM Provider")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/chat/llm/provider",
            json={"provider": "local_llm"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Switched to: {data.get('provider')}")
            print(f"  Message: {data.get('message')}")
            return True
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_list_models():
    """Test listing available local LLM models"""
    print_header("TEST 5: List Available Models")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chat/llm/models")
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Found {data.get('count', 0)} models")
            for model in data.get('models', []):
                print(f"  - {model.get('id', 'unknown')}")
            return True
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_chatbot_query():
    """Test FHIR chatbot with a simple query"""
    print_header("TEST 6: FHIR Chatbot Query")
    
    question = "How many patients do we have?"
    print(f"Question: {question}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/chat/query",
            json={"question": question},
            headers={"Content-Type": "application/json"},
            timeout=60  # Local LLM can be slower
        )
        if response.status_code == 200:
            data = response.json()
            print(f"\n[OK] Chatbot Response:")
            print(f"  Answer: {data.get('answer', '')}")
            print(f"  Results Count: {data.get('results_count', 0)}")
            print(f"  Response Time: {data.get('response_time', 0)}s")
            if data.get('did_fallback'):
                print(f"  [WARNING] Query used fallback mode")
            return True
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_switch_to_gemini():
    """Test switching back to Gemini"""
    print_header("TEST 7: Switch Back to Gemini")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/chat/llm/provider",
            json={"provider": "gemini"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Switched to: {data.get('provider')}")
            return True
        else:
            print(f"[FAIL] Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  LOCAL LLM INTEGRATION TEST SUITE")
    print("="*60)
    
    results = {
        "passed": 0,
        "failed": 0
    }
    
    # Test 1: Local LLM Server
    local_llm_available = test_local_llm_server()
    if local_llm_available:
        results["passed"] += 1
    else:
        results["failed"] += 1
        print("\n[WARNING] Local LLM server not available. Some tests will be skipped.")
    
    # Test 2: Backend Connection
    if test_backend_connection():
        results["passed"] += 1
    else:
        results["failed"] += 1
        print("\n[ERROR] Cannot connect to backend. Stopping tests.")
        print_results(results)
        return
    
    # Test 3: Get Current Provider
    success, provider_data = test_get_current_provider()
    if success:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Only run provider switching tests if local LLM is available
    if local_llm_available:
        # Test 4: Switch to Local LLM
        if test_switch_to_local_llm():
            results["passed"] += 1
            
            # Test 5: List Models
            if test_list_models():
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            # Test 6: Chatbot Query
            if test_chatbot_query():
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            # Test 7: Switch Back
            if test_switch_to_gemini():
                results["passed"] += 1
            else:
                results["failed"] += 1
        else:
            results["failed"] += 4  # Skip remaining tests
    else:
        print("\n[SKIP] Tests 4-7 skipped (local LLM not available)")
    
    # Print Results
    print_results(results)


def print_results(results):
    """Print test results summary"""
    print_header("TEST RESULTS SUMMARY")
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Total:  {results['passed'] + results['failed']}")
    
    if results['failed'] == 0:
        print(f"\n[OK] All tests passed!")
    else:
        print(f"\n[WARNING] Some tests failed. Check output above for details.")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test suite cancelled by user")
        sys.exit(1)

