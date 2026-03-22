import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from founder_bi_agent.backend.tools.monday_bi_tools import MondayBITools
from founder_bi_agent.backend.core.config import AgentSettings
from founder_bi_agent.backend.sql.duckdb_engine import DuckDBSession

def check_data_quality():
    settings = AgentSettings.from_env()
    tools = MondayBITools(settings)
    tables = tools.client.fetch_relevant_tables()
    db = DuckDBSession()
    db.register_tables(tables)
    
    print("--- DEALS DATA QUALITY ---")
    df_deals = tables['deals']
    col = 'masked_deal_value'
    if col in df_deals.columns:
        samples = df_deals[col].dropna().unique()[:10]
        print(f"Sample raw values for {col}: {list(samples)}")
        
        # Check DuckDB casting
        sql = f"SELECT {col}, TRY_CAST({col} AS DOUBLE) as casted FROM deals WHERE {col} IS NOT NULL LIMIT 10"
        casted_df = db.query(sql)
        print("DuckDB Casting Results:")
        print(casted_df)
    else:
        print(f"ERROR: {col} NOT FOUND IN DEALS")

    print("\n--- WORK_ORDERS DATA QUALITY ---")
    df_wo = tables['work_orders']
    col_wo = 'amount_in_rupees_incl_of_gst_masked'
    if col_wo in df_wo.columns:
        samples = df_wo[col_wo].dropna().unique()[:10]
        print(f"Sample raw values for {col_wo}: {list(samples)}")
        
        sql = f"SELECT {col_wo}, TRY_CAST({col_wo} AS DOUBLE) as casted FROM work_orders WHERE {col_wo} IS NOT NULL LIMIT 10"
        casted_df = db.query(sql)
        print("DuckDB Casting Results:")
        print(casted_df)

if __name__ == "__main__":
    check_data_quality()
