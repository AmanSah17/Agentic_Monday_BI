from __future__ import annotations

import json
from typing import Any

import anyio
import pandas as pd
import requests
from fastmcp import Client

from founder_bi_agent.backend.config import AgentSettings


class MondayLiveClient:
    """
    Live monday.com connector.
    - graphql mode: direct monday GraphQL API using token.
    - mcp mode: tool calls through monday MCP server.
    """

    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.mode = settings.monday_mode
        if self.mode not in {"graphql", "mcp"}:
            raise ValueError("MONDAY_MODE must be either 'graphql' or 'mcp'.")

    def get_board_schemas(self) -> list[dict[str, Any]]:
        if self.mode == "mcp":
            payload = self._mcp_list_boards()
            return self._normalize_board_schema_payload(payload)
        return self._graphql_list_boards()

    def get_board_items(self, board_id: int, limit_per_page: int = 200) -> list[dict[str, Any]]:
        if self.mode == "mcp":
            payload = self._mcp_get_board_items(board_id=board_id, limit=limit_per_page)
            return self._normalize_item_payload(payload)
        return self._graphql_get_board_items(board_id=board_id, limit_per_page=limit_per_page)

    def fetch_relevant_tables(self) -> dict[str, pd.DataFrame]:
        schemas = self.get_board_schemas()
        selected: list[dict[str, Any]] = []
        for board in schemas:
            board_name = str(board.get("name", "")).strip().lower()
            if board_name in {
                self.settings.monday_deals_board_name.strip().lower(),
                self.settings.monday_work_orders_board_name.strip().lower(),
            }:
                selected.append(board)

        if len(selected) != 2:
            raise RuntimeError(
                "Strict board scope enforcement failed. Expected exactly two boards: "
                f"'{self.settings.monday_deals_board_name}' and "
                f"'{self.settings.monday_work_orders_board_name}'."
            )

        tables: dict[str, pd.DataFrame] = {}
        for board in selected:
            board_id = int(board["id"])
            board_name = str(board["name"])
            rows = self.get_board_items(board_id=board_id, limit_per_page=200)
            table_name = "deals" if board_name == self.settings.monday_deals_board_name else "work_orders"
            tables[table_name] = pd.DataFrame(rows)
        return tables

    def _graphql_post(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.monday_api_token:
            raise RuntimeError("MONDAY_API_TOKEN is required for graphql mode.")

        response = requests.post(
            self.settings.monday_api_url,
            json={"query": query, "variables": variables},
            headers={
                "Authorization": self.settings.monday_api_token,
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_response": response.text}

        if not response.ok:
            raise RuntimeError(
                f"monday HTTP error {response.status_code}: {payload}"
            )
        if payload.get("errors"):
            raise RuntimeError(f"monday GraphQL error: {payload['errors']}")
        if "data" not in payload:
            raise RuntimeError(f"monday GraphQL missing data field: {payload}")
        return payload["data"]

    def _graphql_list_boards(self) -> list[dict[str, Any]]:
        query = """
        query ($limit: Int!, $page: Int!) {
          boards(limit: $limit, page: $page) {
            id
            name
            board_kind
            columns {
              id
              title
              type
            }
          }
        }
        """
        page = 1
        limit = 100
        out: list[dict[str, Any]] = []
        while True:
            data = self._graphql_post(query=query, variables={"limit": limit, "page": page})
            batch = data.get("boards", [])
            if not batch:
                break
            out.extend(batch)
            if len(batch) < limit:
                break
            page += 1
        return out

    def _graphql_get_board_items(self, board_id: int, limit_per_page: int = 200) -> list[dict[str, Any]]:
        query = """
        query ($board_id: [ID!], $limit: Int!, $cursor: String) {
          boards(ids: $board_id) {
            id
            name
            items_page(limit: $limit, cursor: $cursor) {
              cursor
              items {
                id
                name
                created_at
                updated_at
                group {
                  id
                  title
                }
                column_values {
                  id
                  type
                  text
                  value
                  column {
                    id
                    title
                  }
                }
              }
            }
          }
        }
        """

        cursor: str | None = None
        rows: list[dict[str, Any]] = []

        while True:
            data = self._graphql_post(
                query=query,
                variables={
                    "board_id": [str(board_id)],
                    "limit": limit_per_page,
                    "cursor": cursor,
                },
            )
            boards = data.get("boards", [])
            if not boards:
                break

            page_block = boards[0].get("items_page") or {}
            items = page_block.get("items", [])
            cursor = page_block.get("cursor")

            for item in items:
                base = {
                    "item_id": item.get("id"),
                    "item_name": item.get("name"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "group_id": (item.get("group") or {}).get("id"),
                    "group_title": (item.get("group") or {}).get("title"),
                }
                for col in item.get("column_values", []) or []:
                    col_title = ((col.get("column") or {}).get("title") or col.get("id") or "").strip()
                    if not col_title:
                        continue
                    key = self._safe_column_name(col_title)
                    base[key] = col.get("text")
                    base[f"{key}__raw"] = col.get("value")
                rows.append(base)

            if not cursor:
                break
        return rows

    def _mcp_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async def _run() -> dict[str, Any]:
            async with Client(self.settings.monday_mcp_server_url) as client:
                result = await client.call_tool(tool_name, arguments)
                if hasattr(result, "data") and isinstance(result.data, dict):
                    return result.data
                if isinstance(result, dict):
                    return result
                raise RuntimeError(f"Unexpected MCP result type for tool '{tool_name}'.")

        return anyio.run(_run)

    def _mcp_list_boards(self) -> dict[str, Any]:
        return self._mcp_call(self.settings.monday_mcp_tool_list_boards, {})

    def _mcp_get_board_items(self, board_id: int, limit: int) -> dict[str, Any]:
        return self._mcp_call(
            self.settings.monday_mcp_tool_get_board_items,
            {"board_id": board_id, "limit": limit},
        )

    @staticmethod
    def _normalize_board_schema_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("boards", "data", "items"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return []

    @staticmethod
    def _normalize_item_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("rows", "items", "data"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return []

    @staticmethod
    def _table_name_from_board(board_name: str) -> str:
        normalized = board_name.strip().lower().replace(" ", "_").replace("-", "_")
        return "".join(ch for ch in normalized if ch.isalnum() or ch == "_")

    @staticmethod
    def _safe_column_name(col_name: str) -> str:
        normalized = col_name.strip().lower().replace(" ", "_").replace("-", "_")
        cleaned = "".join(ch for ch in normalized if ch.isalnum() or ch == "_")
        return cleaned or "unnamed_column"

    @staticmethod
    def parse_json_cell(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            return None
        if not (value.startswith("{") or value.startswith("[")):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
