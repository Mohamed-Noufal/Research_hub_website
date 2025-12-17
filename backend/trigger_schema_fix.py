
import requests
import json

def trigger_fix():
    print("🛠️ Triggering Schema Fix via API...")
    try:
        # Note: endpoint is under /users router prefix, so /api/v1/users/debug/fix-schema
        url = "http://localhost:8000/api/v1/users/debug/fix-schema"
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
    except Exception as e:
        print(f"❌ Failed to trigger fix: {e}")

if __name__ == "__main__":
    trigger_fix()
