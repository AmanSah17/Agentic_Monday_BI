"""Test REST and WebSocket endpoints"""
import requests
import asyncio
import websockets
import json

print("=" * 60)
print("🔍 DEBUGGING BACKEND CONNECTIONS")
print("=" * 60)

# Test 1: REST Health Check
print("\n1️⃣  Testing REST endpoint...")
try:
    response = requests.get("http://localhost:8000/ws/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✅ REST routing works!")
except Exception as e:
    print(f"   ❌ REST failed: {e}")

# Test 2: Check main endpoints
print("\n2️⃣  Checking main API...")
try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   API test: {e}")

# Test 3: WebSocket Connection
print("\n3️⃣  Testing WebSocket endpoint...")
async def test_ws():
    try:
        uri = "ws://localhost:8000/ws/execute/test-123"
        print(f"   Connecting to: {uri}")
        
        async with websockets.connect(uri) as ws:
            print("   ✅ WebSocket connected!")
            
            # Send ping
            await ws.send(json.dumps({"type": "ping"}))
            response = json.loads(await ws.recv())
            print(f"   Response: {response}")
            
            return True
    except Exception as e:
        print(f"   ❌ WebSocket failed: {type(e).__name__}: {e}")
        return False

asyncio.run(test_ws())

print("\n" + "=" * 60)
