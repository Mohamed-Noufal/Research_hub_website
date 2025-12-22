"""
Verification script for Phase 5: API & Frontend Integration
Tests the implementation of Agent API endpoints and WebSocket connection
"""
import sys
import os
import asyncio
import httpx
import json
import websockets
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.config import settings

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

BASE_URL = "http://localhost:8000/api/v1"
WS_URL = "ws://localhost:8000/api/v1/agent/ws"


async def test_api_endpoints():
    print("🧪 Testing API Endpoints...")
    
    async with httpx.AsyncClient() as client:
        # 0. Initialize User
        print("\n0. Initializing User...")
        response = await client.post(f"{BASE_URL}/users/init")
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data["user_id"]
            print(f"✅ User initialized: {user_id}")
        else:
            print(f"❌ Failed to initialize user: {response.text}")
            return

        # 0.5 Create Project
        print("\n0.5 Creating Project...")
        response = await client.post(
            f"{BASE_URL}/users/literature-reviews",
            json={"title": "Test Project", "description": "Created by verification script"}
        )
        if response.status_code == 200:
            project_data = response.json()
            project_id = project_data["id"]
            print(f"✅ Project created: {project_id}")
        else:
            print(f"❌ Failed to create project: {response.text}")
            # Try to proceed with None or 1, but likely fail. default to None if fail?
            # actually better to fail here.
            return

        # 1. Create Conversation
        print("\n1. Testing POST /agent/conversations...")
        response = await client.post(
            f"{BASE_URL}/agent/conversations",
            json={"user_id": user_id, "title": "Verification Chat", "project_id": project_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            conversation_id = data["id"]
            print(f"✅ Conversation created: {conversation_id}")
        else:
            print(f"❌ Failed to create conversation: {response.text}")
            return

        # 2. Send Message (REST)
        print("\n2. Testing POST /agent/chat (REST)...")
        response = await client.post(
            f"{BASE_URL}/agent/chat",
            json={
                "message": "Hello, are you working?",
                "user_id": user_id,
                "project_id": project_id
            },
            params={"conversation_id": conversation_id}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ REST Chat response: {data['content'][:50]}...")
        else:
            print(f"❌ REST Chat failed: {response.text}")

        # 3. Get History
        print("\n3. Testing GET /agent/conversations/{id}/history...")
        response = await client.get(
            f"{BASE_URL}/agent/conversations/{conversation_id}/history"
        )
        
        if response.status_code == 200:
            history = response.json()
            print(f"✅ History retrieved: {len(history)} messages")
        else:
            print(f"❌ Failed to get history: {response.text}")

        return conversation_id, user_id, project_id

async def test_websocket(conversation_id, user_id, project_id):
    print(f"\n4. Testing WebSocket connection for conversation {conversation_id}...")
    
    uri = f"{WS_URL}/{conversation_id}?user_id={user_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")

            
            # Send message
            msg = {
                "message": "Tell me a short joke about recursion.",
                "project_id": project_id,
                "user_id": user_id
            }
            await websocket.send(json.dumps(msg))
            print("✅ Message sent via WebSocket")
            
            # Receive responses
            print("Waiting for responses...")
            received_messages = 0
            while received_messages < 3: # Expect at least start, content, end
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    print(f"Received ({data.get('type')}): {str(data)[:100]}...")
                    
                    if data.get('type') == 'message_end':
                        print("✅ Stream completed signal received")
                        break
                    
                    received_messages += 1
                except asyncio.TimeoutError:
                    print("⚠️ Timeout waiting for WebSocket message")
                    break
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    # Ensure server is running before running this test!
    print("⚠️  Make sure the backend server is running on localhost:8000")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run tests
        result = loop.run_until_complete(test_api_endpoints())
        if result:
            conv_id, user_id, project_id = result
            loop.run_until_complete(test_websocket(conv_id, user_id, project_id))
            
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Unexpected error: {repr(e)}")
