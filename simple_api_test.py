#!/usr/bin/env python3
"""Simple API test with better error handling"""
import sys
print("Starting test...")
print(f"Python version: {sys.version}")

# Test /ws/health first (known to work)
print("\n1. Testing /ws/health...")
try:
    import urllib.request
    r = urllib.request.urlopen('http://localhost:8000/ws/health', timeout=3)
    print(f"✅ /ws/health: {r.status}")
except Exception as e:
    print(f"❌ /ws/health error: {e}")

# Test /api/health with extended timeout
print("\n2. Testing /api/health...")
try:
    import urllib.request
    r = urllib.request.urlopen('http://localhost:8000/api/health', timeout=10)
    import json
    data = json.loads(r.read())
    print(f"✅ /api/health: {r.status} - {data}")
except Exception as e:
    print(f"❌ /api/health error: {type(e).__name__}: {e}")

print("\n3. Testing /api/v1/health...")
try:
    import urllib.request
    r = urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=10)
    import json
    data = json.loads(r.read())
    print(f"✅ /api/v1/health: {r.status} - {data}")
except Exception as e:
    print(f"❌ /api/v1/health error: {type(e).__name__}: {e}")

print("\nTest complete!")
