"""
Test script to verify GPT-OSS (LM Studio) connection and API endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:1234"

print("=" * 60)
print("Testing GPT-OSS (LM Studio) Connection")
print("=" * 60)

# Test 1: Check if server is running
print("\n[TEST 1] Checking if server is running...")
try:
    response = requests.get(f"{BASE_URL}/v1/models", timeout=5)
    if response.status_code == 200:
        print("[OK] Server is running")
        data = response.json()
        models = data.get('data', [])
        if models:
            print(f"[OK] Found {len(models)} model(s):")
            for model in models:
                print(f"  - {model.get('id', 'unknown')}")
        else:
            print("[WARNING] No models found - make sure a model is loaded in LM Studio")
    else:
        print(f"[ERROR] Server returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("[ERROR] Cannot connect to server")
    print("  → Make sure LM Studio is running")
    print("  → Click 'Start Server' in LM Studio")
    print("  → Verify it's running on port 1234")
    exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Test 2: Check chat completions endpoint
print("\n[TEST 2] Testing /v1/chat/completions endpoint...")
try:
    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "user", "content": "Say 'test' if you can read this."}
            ],
            "temperature": 0.1,
            "max_tokens": 10
        },
        timeout=30,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("[OK] Chat completions endpoint works!")
        data = response.json()
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0]['message']['content']
            print(f"[OK] Response: {content[:100]}")
        else:
            print("[WARNING] No choices in response")
    elif response.status_code == 405:
        print("[ERROR] Method Not Allowed (405)")
        print("  -> This means the endpoint exists but doesn't accept POST")
        print("  -> Check LM Studio API server settings")
        print("  -> Make sure 'OpenAI Compatible API' is enabled")
    elif response.status_code == 404:
        print("[ERROR] Not Found (404)")
        print("  -> The endpoint /v1/chat/completions doesn't exist")
        print("  -> Check LM Studio API configuration")
    else:
        print(f"[ERROR] Error {response.status_code}: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("[ERROR] Request timed out")
    print("  -> The model might be too slow or not responding")
except requests.exceptions.ConnectionError:
    print("[ERROR] Connection error")
except Exception as e:
    print(f"[ERROR] Error: {e}")

# Test 3: Try with different model name (auto-detect)
print("\n[TEST 3] Testing with auto-detected model...")
try:
    models_resp = requests.get(f"{BASE_URL}/v1/models", timeout=5)
    if models_resp.status_code == 200:
        models_data = models_resp.json()
        if models_data.get('data'):
            model_name = models_data['data'][0].get('id', 'openai/gpt-oss-20b')
            print(f"Using model: {model_name}")
            
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": "Say 'test'"}
                    ],
                    "max_tokens": 10
                },
                timeout=30
            )
            
            if response.status_code == 200:
                print("[OK] Works with auto-detected model!")
            else:
                print(f"[ERROR] Still fails with status {response.status_code}")
except Exception as e:
    print(f"[ERROR] Error: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
print("\nIf all tests pass, the backend should work.")
print("If tests fail, check LM Studio configuration:")

