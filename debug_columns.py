from dotenv import load_dotenv
load_dotenv()
from founder_bi_agent.backend.tools.monday_bi_tools import MondayBITools
from founder_bi_agent.backend.core.config import AgentSettings

def debug_columns():
    settings = AgentSettings.from_env()
    tools = MondayBITools(settings)
    tables = tools.client.fetch_relevant_tables()
    
    for name, df in tables.items():
        print(f"--- {name} ---")
        cols = list(df.columns)
        checks = ["sector", "sectorservice", "execution_status", "invoice_status", "billing_status", "masked_deal_value"]
        for c in checks:
            print(f"{c}: {'EXISTS' if c in cols else 'MISSING'}")

if __name__ == "__main__":
    debug_columns()
