"""
Quick test for the fixed endpoints
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"
PROJECT_ID = 1

print("="*70)
print("TESTING FIXED ENDPOINTS")
print("="*70)

endpoints = [
    f"/projects/{PROJECT_ID}/comparison/config",
    f"/projects/{PROJECT_ID}/synthesis",
    f"/projects/{PROJECT_ID}/analysis/config"
]

for endpoint in endpoints:
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
        print(f"\n{endpoint}")
        print(f"  Status: {status}")
        if response.status_code != 200:
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print(f"\n{endpoint}")
        print(f"  ❌ Error: {e}")

print("\n" + "="*70)
