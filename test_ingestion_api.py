import requests
import json

try:
    response = requests.get("http://localhost:8000/api/v1/ingestion/jobs")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Jobs: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")

