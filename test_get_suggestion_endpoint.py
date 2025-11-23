"""Test script to verify the get-suggestion endpoint is accessible"""
import requests
import json

# Test the endpoint
url = "http://localhost:8002/api/v1/jobs/test_job/get-suggestion"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer demo_token_12345"
}
data = {
    "sourceField": "result_date",
    "sourceType": "string",
    "targetField": "subject.reference",
    "confidence": 0.22,
    "targetResourceType": "Observation"
}

print(f"Testing endpoint: {url}")
print(f"Method: POST")
print(f"Data: {json.dumps(data, indent=2)}")
print()

try:
    response = requests.post(url, json=data, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print(f"[SUCCESS] Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"[ERROR] Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"[ERROR] Request failed: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Status: {e.response.status_code}")
        print(f"Response: {e.response.text}")

