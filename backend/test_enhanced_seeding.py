"""
Test the enhanced seeding functionality with comprehensive template data
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_enhanced_seeding():
    print("="*70)
    print("TESTING ENHANCED LITERATURE REVIEW SEEDING")
    print("="*70)
    
    # 1. Create a new literature review project
    print("\n1. Creating new literature review project...")
    response = requests.post(f"{BASE_URL}/users/literature-reviews", json={
        "title": "Enhanced Template Test Project",
        "description": "Testing comprehensive template data across all tabs"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to create project: {response.status_code}")
        print(response.text)
        return False
    
    project_data = response.json()
    project_id = project_data.get("id")
    print(f"✅ Created project ID: {project_id}")
    
    # 2. Seed with demo data
    print("\n2. Seeding project with comprehensive template data...")
    response = requests.post(f"{BASE_URL}/users/literature-reviews/{project_id}/seed")
    
    if response.status_code != 200:
        print(f"❌ Failed to seed project: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Project seeded successfully")
    
    # 3. Test all tabs
    print("\n3. Verifying template data across all tabs...")
    print("-"*70)
    
    results = {
        "methodology": False,
        "findings": False,
        "gaps": False,
        "comparison_config": False,
        "comparison_attributes": False,
        "synthesis": False,
        "analysis": False
    }
    
    # Test Methodology Tab
    print("\n📚 METHODOLOGY TAB:")
    response = requests.get(f"{BASE_URL}/projects/{project_id}/methodology")
    if response.status_code == 200:
        data = response.json()
        papers = data.get("papers", [])
        print(f"  ✅ {len(papers)} papers with methodology data")
        if len(papers) >= 5:
            print(f"  Sample: {papers[0]['title'][:50]}...")
            print(f"  Description: {papers[0].get('methodology_description', '')[:80]}...")
            results["methodology"] = True
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test Findings Tab
    print("\n🔍 FINDINGS TAB:")
    response = requests.get(f"{BASE_URL}/projects/{project_id}/findings")
    if response.status_code == 200:
        data = response.json()
        findings = data.get("findings", [])
        print(f"  ✅ {len(findings)} papers with findings data")
        if len(findings) >= 5:
            print(f"  Sample finding: {findings[0].get('key_finding', '')[:80]}...")
            results["findings"] = True
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test Research Gaps
    print("\n🎯 RESEARCH GAPS:")
    response = requests.get(f"{BASE_URL}/projects/{project_id}/gaps")
    if response.status_code == 200:
        data = response.json()
        gaps = data.get("gaps", [])
        print(f"  ✅ {len(gaps)} research gaps identified")
        if len(gaps) >= 4:
            print(f"  Sample gap: {gaps[0]['description'][:60]}...")
            print(f"  Priority: {gaps[0]['priority']}")
            results["gaps"] = True
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test Comparison Config
    print("\n🔄 COMPARISON TAB:")
    response = requests.get(f"{BASE_URL}/projects/{project_id}/comparison/config")
    if response.status_code == 200:
        data = response.json()
        selected = data.get("selected_paper_ids", [])
        print(f"  ✅ {len(selected)} papers selected for comparison")
        print(f"  Similarities: {data.get('insights_similarities', '')[:60]}...")
        results["comparison_config"] = True
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test Comparison Attributes
    response = requests.get(f"{BASE_URL}/projects/{project_id}/comparison/attributes")
    if response.status_code == 200:
        data = response.json()
        attributes = data.get("attributes", {})
        print(f"  ✅ {len(attributes)} comparison attributes")
        if len(attributes) > 0:
            sample_key = list(attributes.keys())[0]
            print(f"  Sample: {sample_key} = {attributes[sample_key]}")
            results["comparison_attributes"] = True
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test Synthesis Tab
    print("\n🧩 SYNTHESIS TAB:")
    response = requests.get(f"{BASE_URL}/projects/{project_id}/synthesis")
    if response.status_code == 200:
        data = response.json()
        columns = data.get("columns", [])
        rows = data.get("rows", [])
        cells = data.get("cells", {})
        print(f"  ✅ {len(columns)} columns x {len(rows)} rows")
        print(f"  ✅ {len(cells)} cells populated")
        if len(cells) > 0:
            sample_key = list(cells.keys())[0]
            print(f"  Sample cell: {cells[sample_key][:60]}...")
            results["synthesis"] = True
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Test Analysis Tab
    print("\n📈 ANALYSIS TAB:")
    response = requests.get(f"{BASE_URL}/projects/{project_id}/analysis/config")
    if response.status_code == 200:
        data = response.json()
        prefs = data.get("chart_preferences", {})
        print(f"  ✅ Chart preferences configured")
        print(f"  Methodology chart: {prefs.get('methodology_chart_type')}")
        print(f"  Timeline chart: {prefs.get('timeline_chart_type')}")
        results["analysis"] = True
    else:
        print(f"  ❌ Failed: {response.status_code}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nTabs with template data: {passed}/{total}")
    
    for tab, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {tab}")
    
    if passed == total:
        print("\n🎉 SUCCESS! All tabs populated with comprehensive template data!")
        print("\nUsers will now see a fully functional literature review example")
        print("with realistic data across all tabs when they seed a new project.")
        return True
    else:
        print(f"\n⚠️ {total - passed} tabs failed to populate")
        return False

if __name__ == "__main__":
    try:
        success = test_enhanced_seeding()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Backend server not running at http://localhost:8000")
        print("Please start the server with: uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
