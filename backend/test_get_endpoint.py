"""
Test GET literature reviews endpoint directly
"""
import requests
import json

try:
    response = requests.get("http://localhost:8000/api/v1/users/literature-reviews")
    
    print("="*70)
    print("GET /api/v1/users/literature-reviews")
    print("="*70)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS")
        print(f"Reviews: {len(data.get('reviews', []))}")
        print(f"\nResponse:")
        print(json.dumps(data, indent=2))
    else:
        print(f"\n❌ FAILED")
        print(f"\nResponse:")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
