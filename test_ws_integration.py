#!/usr/bin/env python3
"""Test WebSocket integration with proper error handling"""
import json
import asyncio
import websockets

async def test_websocket():
    from founder_bi_agent.backend.core.auth import create_access_token
    token = create_access_token(data={"sub": "test_user", "user_id": 1})
    uri = f"ws://localhost:8010/ws/execute/test-session-{int(asyncio.get_event_loop().time())}?token={token}"
    
    print(f"🔌 Connecting to WebSocket: {uri}")
    print("=" * 70)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Test 1: Ping/Pong
            print("\n📤 Test 1: Ping/Pong")
            await websocket.send(json.dumps({"type": "ping"}))
            response = json.loads(await websocket.recv())
            print(f"   Response: {response}")
            assert response.get("type") == "pong"
            print("   ✅ Ping/Pong working!")
            
            # Test 2: Get trace (no trace yet)
            print("\n📤 Test 2: Get Trace")
            await websocket.send(json.dumps({"type": "get_trace"}))
            response = json.loads(await websocket.recv())
            print(f"   Response type: {response.get('type')}")
            print(f"   Data keys: {list(response.get('data', {}).keys())}")
            print("   ✅ Get trace working!")
            
            # Test 3: Send execution request
            print("\n📤 Test 3: Execution Request")
            await websocket.send(json.dumps({
                "type": "execute",
                "query": "Show me top deals",
                "context": {"board_id": "test"}
            }))
            
            # Receive execution_start event
            response = json.loads(await websocket.recv())
            print(f"   First response type: {response.get('type')}")
            assert response.get("type") == "execution_start"
            print("   ✅ Execution started!")
            
            # Receive execution_complete event
            response = json.loads(await websocket.recv())
            print(f"   Second response type: {response.get('type')}")
            assert response.get("type") == "execution_complete"
            print("   ✅ Execution completed!")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ ALL WEBSOCKET TESTS PASSED!")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_websocket())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
        exit(1)
