"""
Direct test of comparison endpoint to see actual error
"""
import requests
import json

try:
    response = requests.get("http://localhost:8000/api/v1/projects/1/comparison/config")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ SUCCESS")
        print(json.dumps(response.json(), indent=2))
    else:
        print("❌ ERROR")
        print(response.text)
except Exception as e:
    print(f"❌ Exception: {e}")
