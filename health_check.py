import requests
try:
    resp = requests.get("http://localhost:8010/api/v1/health", timeout=5)
    print(f"Health check status: {resp.status_code}")
    print(f"Health check body: {resp.json()}")
except Exception as e:
    print(f"Health check failed: {e}")
