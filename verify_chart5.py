from fastapi.testclient import TestClient
from founder_bi_agent.backend.main import app
import json

def verify_chart5():
    client = TestClient(app)
    resp = client.get("/api/analytics/dashboard-all")
    assert resp.status_code == 200
    data = resp.json()["data"]
    
    velocity = data.get("executionVelocity", [])
    print(f"Total entries in executionVelocity: {len(velocity)}")
    
    if len(velocity) > 0:
        print("First 5 entries:")
        for item in velocity[:5]:
            print(f"- {item['execution_status']} ({item['type']}): Volume={item['project_count']}, Velocity={item['avg_days_to_bill']}")
            
        # Verify keys
        required_keys = ["execution_status", "type", "project_count", "avg_days_to_bill"]
        for key in required_keys:
            assert key in velocity[0], f"Missing key {key}"
            
    else:
        print("ERROR: executionVelocity is still empty!")

if __name__ == "__main__":
    verify_chart5()
