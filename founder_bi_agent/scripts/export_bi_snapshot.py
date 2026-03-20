from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from founder_bi_agent.backend.config import AgentSettings
from founder_bi_agent.backend.tools.monday_bi_tools import MondayBITools


def main() -> None:
    settings = AgentSettings.from_env()
    tools = MondayBITools(settings)

    deals_df, deals_board_schema = tools.fetch_deals_table()
    work_orders_df, work_orders_board_schema = tools.fetch_work_orders_table()

    deals_table_schema_df = tools.infer_table_schema(deals_df, "deals")
    work_orders_table_schema_df = tools.infer_table_schema(work_orders_df, "work_orders")

    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(__file__).resolve().parents[1] / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    deals_data_path = out_dir / f"deals_rows_{ts}.csv"
    wo_data_path = out_dir / f"work_orders_rows_{ts}.csv"
    deals_schema_path = out_dir / f"deals_table_schema_{ts}.csv"
    wo_schema_path = out_dir / f"work_orders_table_schema_{ts}.csv"
    board_schema_path = out_dir / f"bi_board_schema_{ts}.json"

    deals_df.to_csv(deals_data_path, index=False)
    work_orders_df.to_csv(wo_data_path, index=False)
    deals_table_schema_df.to_csv(deals_schema_path, index=False)
    work_orders_table_schema_df.to_csv(wo_schema_path, index=False)

    payload = {
        "deals_board_schema": deals_board_schema,
        "work_orders_board_schema": work_orders_board_schema,
    }
    with board_schema_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)

    print(f"Saved: {deals_data_path}")
    print(f"Saved: {wo_data_path}")
    print(f"Saved: {deals_schema_path}")
    print(f"Saved: {wo_schema_path}")
    print(f"Saved: {board_schema_path}")


if __name__ == "__main__":
    main()
