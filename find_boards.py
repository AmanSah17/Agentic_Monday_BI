
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load from specific path as in service.py
project_root_env = Path("f:/PyTorch_GPU/Agentic_Monday_BI/.env")
load_dotenv(dotenv_path=project_root_env)

token = os.getenv("MONDAY_COM_API_KEY") or os.getenv("MONDAY_API_TOKEN")
url = "https://api.monday.com/v2"

query = "{ boards(limit: 100) { id name } }"
headers = {
    "Authorization": token,
    "API-Version": "2024-01"
}

print(f"Checking boards with token starting with {token[:10] if token else 'None'}...")
try:
    resp = requests.post(url, json={"query": query}, headers=headers, timeout=10)
    if resp.ok:
        data = resp.json()
        boards = data.get("data", {}).get("boards", [])
        if not boards:
          print("No boards found. Check API token or permissions.")
        for b in boards:
            print(f"BOARD: ID={b['id']}, NAME='{b['name']}'")
    else:
        print(f"Error: {resp.status_code} - {resp.text}")
except Exception as e:
    print(f"Failed: {e}")
