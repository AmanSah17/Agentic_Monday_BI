import requests
import uuid
import time

BASE_URL = "http://localhost:8010/api/v1"

def test_auth_flow():
    # 1. Register User A
    user_a = {
        "username": f"user_a_{uuid.uuid4().hex[:6]}",
        "password": "password123",
        "email": "user_a@example.com"
    }
    print(f"Registering User A: {user_a['username']}...")
    resp = requests.post(f"{BASE_URL}/user/register", json=user_a)
    assert resp.status_code == 200
    print("User A registered.")

    # 2. Login User A
    print("Logging in User A...")
    resp = requests.post(f"{BASE_URL}/user/login", data={"username": user_a["username"], "password": user_a["password"]})
    assert resp.status_code == 200
    token_a = resp.json()["access_token"]
    print("User A logged in. Token received.")

    # 3. Get /me for User A
    resp = requests.get(f"{BASE_URL}/user/me", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == user_a["username"]
    user_a_id = resp.json()["id"]
    print(f"User A /me verified. ID: {user_a_id}")

    # 4. Create history for User A
    session_id = str(uuid.uuid4())
    print(f"Creating history for User A (Session: {session_id})...")
    query_payload = {
        "question": "Who is User A?",
        "conversation_history": [],
        "session_id": session_id
    }
    resp = requests.post(f"{BASE_URL}/chat/query", json=query_payload, headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    print("User A query successful.")

    # 5. Verify User A history
    resp = requests.get(f"{BASE_URL}/chat/history/{session_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    assert len(resp.json()["history"]) >= 2
    print("User A history verified.")

    # 6. Register & Login User B
    user_b = {
        "username": f"user_b_{uuid.uuid4().hex[:6]}",
        "password": "password123"
    }
    print(f"Registering User B: {user_b['username']}...")
    resp = requests.post(f"{BASE_URL}/user/register", json=user_b)
    assert resp.status_code == 200
    token_b = requests.post(f"{BASE_URL}/user/login", data={"username": user_b["username"], "password": user_b["password"]}).json()["access_token"]
    print("User B logged in.")

    # 7. Try to access User A's history with User B's token
    print("Attempting to access User A's history with User B's token (should be empty/isolated)...")
    resp = requests.get(f"{BASE_URL}/chat/history/{session_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 200
    assert len(resp.json()["history"]) == 0
    print("Isolation verified: User B cannot see User A's session history.")

    print("\nALL AUTH TESTS PASSED!")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
