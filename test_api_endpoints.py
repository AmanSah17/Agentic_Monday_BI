#!/usr/bin/env python3
"""Test API endpoints to debug backend errors"""
import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None):
    """Test an endpoint and return response"""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"Testing: {method} {path}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            with urllib.request.urlopen(url, timeout=5) as response:
                content = response.read().decode()
                status = response.status
                print(f"✅ Status: {status}")
                try:
                    print(f"Response: {json.dumps(json.loads(content), indent=2)}")
                except:
                    print(f"Response: {content[:500]}")
        elif method == "POST":
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode() if data else b'{}',
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read().decode()
                status = response.status
                print(f"✅ Status: {status}")
                try:
                    print(f"Response: {json.dumps(json.loads(content), indent=2)[:500]}")
                except:
                    print(f"Response: {content[:500]}")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        try:
            content = e.read().decode()
            print(f"Error Response: {content[:500]}")
        except:
            pass
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

# Test the health endpoints
test_endpoint("GET", "/api/health")
test_endpoint("GET", "/ws/health")

# Test with a sample query
test_endpoint("POST", "/api/query", {
    "question": "How many deals are in the pipeline?",
    "conversation_history": [],
    "session_id": "test-session"
})

# Test dashboard endpoint
test_endpoint("GET", "/api/analytics/dashboard-all")
