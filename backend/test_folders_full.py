import requests
import json
import os

BASE_URL = "http://localhost:8000/api/v1"

def print_step(step):
    print(f"\n{'='*20} {step} {'='*20}")

def test_folders_workflow():
    print("🚀 Starting Folder System Test...")

    # 1. Create a Manual Paper
    print_step("1. Creating Manual Paper")
    paper_data = {
        "title": "Test Paper for Folders",
        "authors": "Test Author",
        "abstract": "This is a test paper created to test folder functionality.",
        "year": 2024,
        "venue": "Test Venue"
    }
    
    # We'll send this as form data
    response = requests.post(f"{BASE_URL}/papers/manual", data=paper_data)
    
    if response.status_code != 200:
        try:
            error_detail = response.json().get("detail", response.text)
            print(f"❌ Failed to create paper: {str(error_detail)[:200]}")
        except:
            print(f"❌ Failed to create paper: {response.text[:200]}")
        return
    
    paper = response.json()
    paper_id = paper["id"]
    print(f"✅ Paper created successfully! ID: {paper_id}")
    print(json.dumps(paper, indent=2))

    # 2. Create a Folder
    print_step("2. Creating Folder")
    folder_data = {
        "name": "Test Folder 1",
        "description": "This is a test folder"
    }
    
    response = requests.post(f"{BASE_URL}/folders", json=folder_data)
    
    if response.status_code != 200:
        print(f"❌ Failed to create folder: {response.text}")
        return
    
    folder = response.json()
    folder_id = folder["id"]
    print(f"✅ Folder created successfully! ID: {folder_id}")
    print(json.dumps(folder, indent=2))

    # 3. List Folders
    print_step("3. Listing Folders")
    response = requests.get(f"{BASE_URL}/folders")
    
    if response.status_code != 200:
        print(f"❌ Failed to list folders: {response.text}")
        return
    
    folders = response.json()
    print(f"✅ Retrieved {len(folders)} folders")
    found = False
    for f in folders:
        if f["id"] == folder_id:
            found = True
            print(f"Found our folder: {f['name']}")
            break
    
    if not found:
        print("❌ Created folder not found in list!")
        return

    # 4. Update Folder
    print_step("4. Updating Folder")
    update_data = {
        "name": "Updated Test Folder",
        "description": "Updated description"
    }
    
    response = requests.put(f"{BASE_URL}/folders/{folder_id}", json=update_data)
    
    if response.status_code != 200:
        print(f"❌ Failed to update folder: {response.text}")
        return
    
    updated_folder = response.json()
    print(f"✅ Folder updated: {updated_folder['name']}")
    if updated_folder["name"] != "Updated Test Folder":
        print("❌ Folder name mismatch!")
        return

    # 5. Add Paper to Folder
    print_step("5. Adding Paper to Folder")
    response = requests.post(f"{BASE_URL}/folders/{folder_id}/papers/{paper_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to add paper to folder: {response.text}")
        return
    
    print(f"✅ Paper added to folder: {response.json()}")

    # 6. Get Folder Papers
    print_step("6. Getting Folder Papers")
    response = requests.get(f"{BASE_URL}/folders/{folder_id}/papers")
    
    if response.status_code != 200:
        print(f"❌ Failed to get folder papers: {response.text}")
        return
    
    folder_papers = response.json()
    print(f"✅ Retrieved folder papers: {folder_papers}")
    
    if paper_id not in folder_papers["paper_ids"]:
        print("❌ Paper ID not found in folder!")
        return
    else:
        print("✅ Paper ID found in folder list")

    # 7. Remove Paper from Folder
    print_step("7. Removing Paper from Folder")
    response = requests.delete(f"{BASE_URL}/folders/{folder_id}/papers/{paper_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to remove paper from folder: {response.text}")
        return
    
    print(f"✅ Paper removed from folder: {response.json()}")
    
    # Verify removal
    response = requests.get(f"{BASE_URL}/folders/{folder_id}/papers")
    folder_papers = response.json()
    if paper_id in folder_papers["paper_ids"]:
        print("❌ Paper still in folder after removal!")
        return
    else:
        print("✅ Verified paper is gone from folder")

    # 8. Delete Folder
    print_step("8. Deleting Folder")
    response = requests.delete(f"{BASE_URL}/folders/{folder_id}")
    
    if response.status_code != 200:
        print(f"❌ Failed to delete folder: {response.text}")
        return
    
    print(f"✅ Folder deleted: {response.json()}")
    
    # Verify deletion
    response = requests.get(f"{BASE_URL}/folders")
    folders = response.json()
    found = False
    for f in folders:
        if f["id"] == folder_id:
            found = True
            break
    
    if found:
        print("❌ Folder still exists after deletion!")
        return
    else:
        print("✅ Verified folder is gone")

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    try:
        test_folders_workflow()
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
