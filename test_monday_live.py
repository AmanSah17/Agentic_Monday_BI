import os
from founder_bi_agent.backend.config import AgentSettings
from founder_bi_agent.backend.mcp.monday_live import MondayLiveClient

from dotenv import load_dotenv

def run():
    load_dotenv()
    settings = AgentSettings.from_env()
    client = MondayLiveClient(settings)
    board_id = 5027339053
    items = client._graphql_get_board_items(board_id, 500) # Internal direct call
    print(f"Total rows fetched: {len(items)}")
    if items:
        row = items[0]
        print("Keys across row 0:")
        for k, v in row.items():
            if not k.endswith("__raw"):
                print(f" - {k}: {str(v)[:50]}")

if __name__ == "__main__":
    run()
