"""Quick WebSocket Connection Test"""
import asyncio
import websockets
import json
import sys

async def test_websocket():
    """Test WebSocket connection and basic message flow"""
    session_id = "test-session-123"
    uri = f"ws://localhost:8000/ws/execute/{session_id}"
    
    try:
        print(f"🔌 Connecting to WebSocket: {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Send a ping message
            print("\n📤 Sending ping message...")
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Receive pong response
            print("⏳ Waiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            print(f"📥 Received: {json.dumps(data, indent=2)}")
            
            if data.get("type") == "pong":
                print("✅ Pong received successfully!")
                return True
            else:
                print("❌ Unexpected response type")
                return False
                
    except asyncio.TimeoutError:
        print("❌ Timeout: No response received within 5 seconds")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused - Backend may not be running")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket())
    sys.exit(0 if success else 1)
