import requests
import json
import time

BASE_URL = "http://localhost:8010/api/v1"

def debug_query():
    # 1. Register/Login Aman
    user_creds = {"username": "Aman", "password": "password123", "email": "aman@example.com"}
    print(f"Attempting to register Aman...")
    try:
        requests.post(f"{BASE_URL}/user/register", json=user_creds)
    except:
        pass # Already exists
    
    print("Logging in...")
    resp = requests.post(f"{BASE_URL}/user/login", data={"username": "Aman", "password": "password123"})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    print(f"Login successful. Token: {token[:10]}...")
    
    # 2. Send query
    query = "how our piepeline doing for energy sector!"
    print(f"Sending query: '{query}'")
    
    start_time = time.time()
    try:
        resp = requests.post(
            f"{BASE_URL}/chat/query",
            json={
                "question": query,
                "conversation_history": [],
                "session_id": "debug_session_energy"
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=60 # Long timeout for graph execution
        )
        duration = time.time() - start_time
        print(f"Response received in {duration:.2f}s (Status: {resp.status_code})")
        print(f"Response Body: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Query failed with exception: {e}")

if __name__ == "__main__":
    debug_query()
