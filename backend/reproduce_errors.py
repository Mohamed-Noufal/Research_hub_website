
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"
PROJECT_ID = 23  # Using ID from user logs
USER_ID = "550e8400-e29b-41d4-a716-446655440000"

def test_comparison_config():
    print("\nTesting Comparison Config GET...")
    try:
        response = requests.get(f"{BASE_URL}/projects/{PROJECT_ID}/comparison/config")
        if response.status_code == 200:
            print("✅ Comparison Config GET Success")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Comparison Config GET Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Comparison Config GET Exception: {e}")

def test_synthesis_patch():
    print("\nTesting Synthesis Cell PATCH...")
    try:
        payload = {
            "row_id": "row1",
            "column_id": "col1",
            "value": "Test Value"
        }
        response = requests.patch(
            f"{BASE_URL}/projects/{PROJECT_ID}/synthesis/cells",
            json=payload
        )
        if response.status_code == 200:
            print("✅ Synthesis Cell PATCH Success")
            print(response.json())
        else:
            print(f"❌ Synthesis Cell PATCH Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Synthesis Cell PATCH Exception: {e}")

if __name__ == "__main__":
    test_comparison_config()
    test_synthesis_patch()
