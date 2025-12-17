
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def print_response(resp, label):
    print(f"\n--- {label} ---")
    print(f"Status: {resp.status_code}")
    try:
        data = resp.json()
        print(json.dumps(data, indent=2))
        return data
    except:
        print(resp.text)
        return None

def test_live():
    print("🚀 Starting Live API Diagnostic...")
    
    # 1. Create Project
    print("\n1. Creating Test Project...")
    resp = requests.post(f"{BASE_URL}/users/literature-reviews", json={
        "title": "Live Diagnostic Project",
        "description": "Testing data flow",
        "paper_ids": []
    })
    
    project_data = print_response(resp, "Create Project")
    if not project_data or 'id' not in project_data:
        print("❌ Failed to create project. Aborting.")
        return
        
    project_id = project_data['id']
    
    # 2. Seed Project
    print(f"\n2. Seeding Project {project_id}...")
    resp = requests.post(f"{BASE_URL}/users/literature-reviews/{project_id}/seed")
    print_response(resp, "Seed Project")
    
    # 3. Get Project Papers (Check Enriched Data)
    print(f"\n3. Fetching Papers for Project {project_id}...")
    resp = requests.get(f"{BASE_URL}/projects/{project_id}/papers")
    papers_data = print_response(resp, "Get Project Papers")
    
    if papers_data and 'papers' in papers_data:
        papers = papers_data['papers']
        print(f"\n✅ Fetched {len(papers)} papers.")
        
        # Check specific fields
        if len(papers) > 0:
            p1 = papers[0]
            print("\n🔎 Inspecting First Paper Data:")
            print(f"   - Title: {p1.get('title')}")
            print(f"   - ID: {p1.get('id')}")
            print(f"   - Methodology Description: {p1.get('methodologyDescription')}")
            print(f"   - Key Findings: {p1.get('keyFindings')}")
            
            if p1.get('methodologyDescription'):
                print("   ✅ Methodology Data Present!")
            else:
                print("   ❌ Methodology Data MISSING (is Null or empty key)")
        else:
            print("   ❌ No papers found after seeding!")
    
    # 4. Cleanup
    print(f"\n4. Deleting Test Project {project_id}...")
    requests.delete(f"{BASE_URL}/users/literature-reviews/{project_id}")
    print("Test Complete.")

if __name__ == "__main__":
    test_live()
