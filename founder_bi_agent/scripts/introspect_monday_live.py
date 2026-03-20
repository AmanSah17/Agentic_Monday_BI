from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

MONDAY_API_URL = "https://api.monday.com/v2"


def safe_col(name: str) -> str:
    normalized = name.strip().lower().replace(" ", "_").replace("-", "_")
    out = "".join(ch for ch in normalized if ch.isalnum() or ch == "_")
    return out or "unnamed_column"


def post_graphql(token: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    resp = requests.post(
        MONDAY_API_URL,
        json={"query": query, "variables": variables},
        headers={"Authorization": token, "Content-Type": "application/json"},
        timeout=60,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]


def list_all_boards(token: str) -> list[dict[str, Any]]:
    query = """
    query ($limit: Int!, $page: Int!) {
      boards(limit: $limit, page: $page) {
        id
        name
        board_kind
        state
        permissions
        workspace {
          id
          name
          kind
        }
        columns {
          id
          title
          type
          settings_str
        }
      }
    }
    """
    all_boards: list[dict[str, Any]] = []
    limit = 100
    page = 1
    while True:
        data = post_graphql(token, query, {"limit": limit, "page": page})
        batch = data.get("boards", [])
        if not batch:
            break
        all_boards.extend(batch)
        if len(batch) < limit:
            break
        page += 1
    return all_boards


def fetch_board_items_sample(token: str, board_id: int, limit: int = 5) -> list[dict[str, Any]]:
    query = """
    query ($board_id: [ID!], $limit: Int!) {
      boards(ids: $board_id) {
        id
        name
        items_page(limit: $limit) {
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
    data = post_graphql(token, query, {"board_id": [str(board_id)], "limit": limit})
    boards = data.get("boards", [])
    if not boards:
        return []
    return (boards[0].get("items_page") or {}).get("items", []) or []


def build_schema_rows(board: dict[str, Any], item_samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    board_id = int(board["id"])
    board_name = str(board["name"])
    rows: list[dict[str, Any]] = []

    meta_columns = [
        ("item_id", "metadata"),
        ("item_name", "metadata"),
        ("created_at", "metadata"),
        ("updated_at", "metadata"),
        ("group_id", "metadata"),
        ("group_title", "metadata"),
    ]
    for col_name, monday_type in meta_columns:
        rows.append(
            {
                "board_id": board_id,
                "board_name": board_name,
                "column_name": col_name,
                "monday_column_id": None,
                "monday_type": monday_type,
                "sample_value": None,
            }
        )

    sample_map: dict[str, str] = {}
    for item in item_samples:
        for col in item.get("column_values", []) or []:
            key = str((col.get("column") or {}).get("title") or col.get("id") or "").strip()
            if not key:
                continue
            if key not in sample_map:
                sample_map[key] = str(col.get("text") or "")

    for col in board.get("columns", []) or []:
        title = str(col.get("title") or col.get("id") or "")
        rows.append(
            {
                "board_id": board_id,
                "board_name": board_name,
                "column_name": safe_col(title),
                "monday_column_id": col.get("id"),
                "monday_type": col.get("type"),
                "sample_value": sample_map.get(title),
            }
        )
    return rows


def main() -> None:
    token = os.getenv("MONDAY_API_TOKEN")
    if not token:
        raise RuntimeError("MONDAY_API_TOKEN is required.")

    boards = list_all_boards(token)
    print(f"Discovered boards: {len(boards)}")

    board_summary_rows: list[dict[str, Any]] = []
    schema_rows: list[dict[str, Any]] = []
    samples_payload: dict[str, Any] = {}

    for board in boards:
        board_id = int(board["id"])
        board_name = str(board["name"])
        sample_items = fetch_board_items_sample(token, board_id=board_id, limit=5)
        samples_payload[str(board_id)] = {
            "board_name": board_name,
            "sample_items": sample_items,
        }

        schema_rows.extend(build_schema_rows(board, sample_items))
        board_summary_rows.append(
            {
                "board_id": board_id,
                "board_name": board_name,
                "board_kind": board.get("board_kind"),
                "state": board.get("state"),
                "permissions": board.get("permissions"),
                "workspace_id": (board.get("workspace") or {}).get("id"),
                "workspace_name": (board.get("workspace") or {}).get("name"),
                "column_count": len(board.get("columns", []) or []),
                "sample_item_count": len(sample_items),
            }
        )
        print(f"Fetched schema + sample rows for board: {board_name} ({board_id})")

    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifacts_dir = Path(__file__).resolve().parents[1] / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    boards_path = artifacts_dir / f"monday_boards_{ts}.json"
    samples_path = artifacts_dir / f"monday_samples_{ts}.json"
    schema_path = artifacts_dir / f"monday_table_schema_{ts}.csv"
    board_summary_path = artifacts_dir / f"monday_board_summary_{ts}.csv"

    with boards_path.open("w", encoding="utf-8") as f:
        json.dump(boards, f, ensure_ascii=True, indent=2)
    with samples_path.open("w", encoding="utf-8") as f:
        json.dump(samples_payload, f, ensure_ascii=True, indent=2)

    pd.DataFrame(schema_rows).to_csv(schema_path, index=False)
    pd.DataFrame(board_summary_rows).to_csv(board_summary_path, index=False)

    print(f"\nSaved: {boards_path}")
    print(f"Saved: {samples_path}")
    print(f"Saved: {schema_path}")
    print(f"Saved: {board_summary_path}")


if __name__ == "__main__":
    main()
