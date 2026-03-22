import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from founder_bi_agent.backend.tools.monday_bi_tools import MondayBITools
from founder_bi_agent.backend.core.config import AgentSettings

def audit_velocity():
    settings = AgentSettings.from_env()
    tools = MondayBITools(settings)
    tables = tools.client.fetch_relevant_tables()
    df = tables['work_orders']
    
    print(f"Total Work Orders: {len(df)}")
    has_start = df['probable_start_date'].notnull()
    has_bill = df['actual_billing_month'].notnull()
    
    print(f"Has probable_start_date: {has_start.sum()}")
    print(f"Has actual_billing_month: {has_bill.sum()}")
    print(f"Has Both: {(has_start & has_bill).sum()}")
    
    if (has_start & has_bill).sum() > 0:
        sample = df[has_start & has_bill][['probable_start_date', 'actual_billing_month']].head(5)
        print("Sample of both dates:")
        print(sample)
    
    # Check execution_status distribution
    print("\nExecution Status Distribution:")
    print(df['execution_status'].value_counts())

if __name__ == "__main__":
    audit_velocity()
