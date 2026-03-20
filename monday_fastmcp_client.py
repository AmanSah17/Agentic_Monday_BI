import asyncio
import os
from pathlib import Path
from typing import Any

import pandas as pd
from fastmcp import Client


def _to_dataframe_schema(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "table": table_name,
            "column": df.columns,
            "dtype": [str(dtype) for dtype in df.dtypes],
            "non_null_count": [int(df[col].notna().sum()) for col in df.columns],
            "null_count": [int(df[col].isna().sum()) for col in df.columns],
        }
    )


def _extract_result_payload(result: Any) -> dict[str, Any]:
    # FastMCP parsed result commonly exposes `.data` for structured outputs.
    if hasattr(result, "data") and isinstance(result.data, dict):
        return result.data
    if isinstance(result, dict):
        return result
    raise RuntimeError("Unexpected tool result format; expected a dictionary payload.")


async def main() -> None:
    server_path = Path(__file__).with_name("monday_fastmcp_server.py")
    api_token = os.getenv("MONDAY_API_TOKEN")
    if not api_token:
        raise RuntimeError("Set MONDAY_API_TOKEN in your environment before running.")

    async with Client(server_path) as client:
        result = await client.call_tool(
            "get_all_boards",
            {"limit_per_page": 100, "api_token": api_token},
        )
        payload = _extract_result_payload(result)

    boards = payload.get("boards", [])
    boards_df = pd.DataFrame(boards)

    if boards_df.empty:
        print("No boards returned.")
        return

    if "workspace" in boards_df.columns:
        workspace_df = pd.json_normalize(boards_df["workspace"]).add_prefix("workspace_")
        boards_df = pd.concat([boards_df.drop(columns=["workspace"]), workspace_df], axis=1)

    columns_records: list[dict[str, Any]] = []
    for board in boards:
        board_id = board.get("id")
        board_name = board.get("name")
        for col in board.get("columns", []) or []:
            columns_records.append(
                {
                    "board_id": board_id,
                    "board_name": board_name,
                    "column_id": col.get("id"),
                    "column_title": col.get("title"),
                    "column_type": col.get("type"),
                    "column_settings_str": col.get("settings_str"),
                }
            )

    board_columns_df = pd.DataFrame(columns_records)

    print("\n=== BOARDS TABLE (preview) ===")
    print(boards_df.head(10).to_string(index=False))
    print(f"\nboards shape: {boards_df.shape}")

    print("\n=== BOARD_COLUMNS TABLE (preview) ===")
    if board_columns_df.empty:
        print("No column metadata returned.")
    else:
        print(board_columns_df.head(10).to_string(index=False))
    print(f"\nboard_columns shape: {board_columns_df.shape}")

    boards_schema_df = _to_dataframe_schema(boards_df, "boards")
    board_columns_schema_df = _to_dataframe_schema(board_columns_df, "board_columns")
    schema_df = pd.concat([boards_schema_df, board_columns_schema_df], ignore_index=True)

    print("\n=== SCHEMA (per table) ===")
    print(schema_df.to_string(index=False))


if __name__ == "__main__":
    asyncio.run(main())
