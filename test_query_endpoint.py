#!/usr/bin/env python3
"""Test the query endpoint"""
import json
import urllib.request
import sys

print("Testing /api/query endpoint...")

payload = {
    "question": "How many deals are in the pipeline?",
    "conversation_history": [],
    "session_id": "test-session-001"
}

print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    req = urllib.request.Request(
        'http://localhost:8000/api/query',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    print("Sending request...")
    with urllib.request.urlopen(req, timeout=30) as response:
        print(f"✅ Status: {response.status}\n")
        data = json.loads(response.read().decode())
        print("Response (first 1000 chars):")
        print(json.dumps(data, indent=2)[:1000])
        
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error {e.code}: {e.reason}\n")
    try:
        error_data = e.read().decode()
        print(f"Error response:\n{error_data[:500]}")
    except:
        pass
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}\n")
    import traceback
    traceback.print_exc()
