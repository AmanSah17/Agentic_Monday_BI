from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from founder_bi_agent.backend.core.config import AgentSettings
from founder_bi_agent.backend.mcp.monday_live import MondayLiveClient


@dataclass
class BoardRef:
    board_id: int
    board_name: str


class MondayBITools:
    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.client = MondayLiveClient(settings)
        self._tool_trace: list[dict[str, Any]] = []

    def pop_trace(self) -> list[dict[str, Any]]:
        out = list(self._tool_trace)
        self._tool_trace = []
        return out

    def _log(self, tool_name: str, params: dict[str, Any], result_meta: dict[str, Any]) -> None:
        self._tool_trace.append(
            {
                "ts": datetime.utcnow().isoformat() + "Z",
                "tool": tool_name,
                "params": params,
                "result_meta": result_meta,
            }
        )

    def list_boards(self) -> list[dict[str, Any]]:
        boards = self.client.get_board_schemas()
        self._log("list_boards", {}, {"count": len(boards)})
        return boards

    def discover_bi_boards(self, boards: list[dict[str, Any]] | None = None) -> dict[str, BoardRef]:
        deals_id = self.settings.monday_deals_board_id
        wo_id = self.settings.monday_work_orders_board_id

        if not boards and deals_id and wo_id:
            # If we have IDs and no boards list, we can fetch just these two
            boards = self.client.get_board_schemas(board_ids=[deals_id, wo_id])
        elif not boards:
            boards = self.list_boards()

        deals = self._resolve_board(
            boards,
            expected_name=self.settings.monday_deals_board_name,
            expected_id=self.settings.monday_deals_board_id,
            board_role="deals",
        )
        work_orders = self._resolve_board(
            boards,
            expected_name=self.settings.monday_work_orders_board_name,
            expected_id=self.settings.monday_work_orders_board_id,
            board_role="work_orders",
        )

        board_map = {"deals": deals, "work_orders": work_orders}
        self._log(
            "discover_bi_boards",
            {
                "deals_expected_name": self.settings.monday_deals_board_name,
                "work_orders_expected_name": self.settings.monday_work_orders_board_name,
            },
            {
                "deals_board_id": deals.board_id,
                "work_orders_board_id": work_orders.board_id,
            },
        )
        return board_map

    def get_board_schema(
        self,
        board_id: int | None = None,
        board_name: str | None = None,
        boards: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if boards is None:
            if board_id is not None:
                # Fetch just this one board
                boards = self.client.get_board_schemas(board_ids=[int(board_id)])
            else:
                boards = self.list_boards()
                
        for board in boards:
            if board_id is not None and int(board["id"]) == int(board_id):
                return board
            if board_name is not None and str(board["name"]).lower() == board_name.lower():
                return board
        raise ValueError("Board not found by board_id/board_name.")

    def fetch_board_table(self, board_id: int) -> pd.DataFrame:
        rows = self.client.get_board_items(board_id=board_id, limit_per_page=200)
        df = pd.DataFrame(rows)
        self._log(
            "fetch_board_table",
            {"board_id": board_id},
            {"rows": len(df), "columns": len(df.columns)},
        )
        return df

    def fetch_deals_table(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        board_map = self.discover_bi_boards()
        if "deals" not in board_map:
            raise RuntimeError("Could not discover a deals board.")
        ref = board_map["deals"]
        df = self.fetch_board_table(ref.board_id)
        schema = self.get_board_schema(board_id=ref.board_id)
        self._log(
            "fetch_deals_table",
            {"board_id": ref.board_id, "board_name": ref.board_name},
            {"rows": len(df), "schema_columns": len(schema.get("columns", []))},
        )
        return df, schema

    def fetch_work_orders_table(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        board_map = self.discover_bi_boards()
        if "work_orders" not in board_map:
            raise RuntimeError("Could not discover a work orders board.")
        ref = board_map["work_orders"]
        df = self.fetch_board_table(ref.board_id)
        schema = self.get_board_schema(board_id=ref.board_id)
        self._log(
            "fetch_work_orders_table",
            {"board_id": ref.board_id, "board_name": ref.board_name},
            {"rows": len(df), "schema_columns": len(schema.get("columns", []))},
        )
        return df, schema

    @staticmethod
    def infer_table_schema(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(
                columns=["table_name", "column_name", "dtype", "non_null_count", "null_count"]
            )
        return pd.DataFrame(
            {
                "table_name": table_name,
                "column_name": df.columns,
                "dtype": [str(x) for x in df.dtypes],
                "non_null_count": [int(df[c].notna().sum()) for c in df.columns],
                "null_count": [int(df[c].isna().sum()) for c in df.columns],
            }
        )

    def fetch_bi_snapshot(self) -> dict[str, Any]:
        deals_df, deals_schema = self.fetch_deals_table()
        wo_df, wo_schema = self.fetch_work_orders_table()

        deals_table_schema = self.infer_table_schema(deals_df, "deals")
        wo_table_schema = self.infer_table_schema(wo_df, "work_orders")

        return {
            "deals_board_schema": deals_schema,
            "work_orders_board_schema": wo_schema,
            "deals_rows": deals_df.to_dict(orient="records"),
            "work_orders_rows": wo_df.to_dict(orient="records"),
            "deals_table_schema": deals_table_schema.to_dict(orient="records"),
            "work_orders_table_schema": wo_table_schema.to_dict(orient="records"),
        }

    def _resolve_board(
        self,
        boards: list[dict[str, Any]],
        expected_name: str,
        expected_id: int | None,
        board_role: str,
    ) -> BoardRef:
        if expected_id is not None:
            for board in boards:
                if int(board.get("id")) == int(expected_id):
                    return BoardRef(
                        board_id=int(board["id"]),
                        board_name=str(board["name"]),
                    )
            raise RuntimeError(
                f"Strict board check failed for {board_role}: id {expected_id} not found."
            )

        for board in boards:
            if str(board.get("name", "")).strip().lower() == expected_name.strip().lower():
                return BoardRef(
                    board_id=int(board["id"]),
                    board_name=str(board["name"]),
                )

        raise RuntimeError(
            f"Strict board check failed for {board_role}: name '{expected_name}' not found."
        )
