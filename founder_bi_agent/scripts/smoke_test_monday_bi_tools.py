from __future__ import annotations

from founder_bi_agent.backend.config import AgentSettings
from founder_bi_agent.backend.tools.monday_bi_tools import MondayBITools


def main() -> None:
    settings = AgentSettings.from_env()
    tools = MondayBITools(settings)

    boards = tools.list_boards()
    print(f"Total boards discovered: {len(boards)}")

    board_map = tools.discover_bi_boards()
    print("Discovered BI boards:")
    for key, ref in board_map.items():
        print(f"- {key}: {ref.board_name} ({ref.board_id})")

    deals_df, deals_schema = tools.fetch_deals_table()
    wo_df, wo_schema = tools.fetch_work_orders_table()

    print(f"\nDeals rows: {len(deals_df)} | columns: {len(deals_df.columns)}")
    print(f"Deals board schema columns: {len(deals_schema.get('columns', []))}")

    print(f"Work Orders rows: {len(wo_df)} | columns: {len(wo_df.columns)}")
    print(f"Work Orders board schema columns: {len(wo_schema.get('columns', []))}")

    deals_table_schema = tools.infer_table_schema(deals_df, "deals")
    wo_table_schema = tools.infer_table_schema(wo_df, "work_orders")
    print(f"\nDeals table schema rows: {len(deals_table_schema)}")
    print(f"Work orders table schema rows: {len(wo_table_schema)}")


if __name__ == "__main__":
    main()
