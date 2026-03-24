import asyncio
import websockets
import json
import requests

BASE_URL = "http://127.0.0.1:8010/api/v1"

async def test_ws():
    # 1. Login to get token
    print("Logging in...")
    try:
        resp = requests.post(f"{BASE_URL}/user/login", data={"username": "Aman", "password": "password123"}, timeout=5)
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        print(f"Token obtained: {token[:10]}...")
    except Exception as e:
        print(f"Login request failed: {e}")
        return

    # 2. Try WebSocket connect
    ws_url = f"ws://127.0.0.1:8010/ws/execute/debug_session?token={token}"
    print(f"Connecting to {ws_url}...")
    try:
        async with websockets.connect(ws_url) as ws:
            print("WebSocket connected successfully!")
            await ws.send(json.dumps({
                "type": "execute",
                "query": "how our pipeline doing for energy sector!",
                "conversation_history": []
            }))
            print("Execution request sent.")
            
            # Wait for events
            while True:
                resp = await asyncio.wait_for(ws.recv(), timeout=20)
                data = json.loads(resp)
                print(f"WS Event: {data.get('type')} - {data.get('node_name', '')}")
                if data.get("type") in ["execution_complete", "execution_error"]:
                    if data.get("type") == "execution_error":
                        print(f"Error: {data.get('error')}")
                    else:
                        print("Execution complete!")
                    break
    except Exception as e:
        print(f"WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
