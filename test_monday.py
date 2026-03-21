import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("MONDAY_COM_API_KEY")

def run():
    url = "https://api.monday.com/v2"
    headers = {
        "Authorization": token,
        "API-Version": "2024-01",
        "Content-Type": "application/json"
    }
    
    query = """
    query {
      boards {
        id
        name
      }
    }
    """
    
    try:
        resp = requests.post(url, json={"query": query}, headers=headers)
        data = resp.json()
        print("ALL BOARDS:")
        target_id = None
        for b in data.get("data", {}).get("boards", []):
            print(f"- {b['id']}: {b['name']}")
            if b['name'] == "Deal funnel Data":
                target_id = b['id']
                
        if target_id:
            print(f"\nQuerying items for target ID: {target_id}")
            q2 = f"""query {{ boards(ids: [{target_id}]) {{ items_page(limit: 1) {{ items {{ name column_values {{ id text value column {{ title }} }} }} }} }} }}"""
            resp2 = requests.post(url, json={"query": q2}, headers=headers)
            print(json.dumps(resp2.json(), indent=2))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    run()
