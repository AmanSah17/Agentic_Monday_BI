import os
from typing import Any

import requests
from fastmcp import FastMCP

MONDAY_API_URL = "https://api.monday.com/v2"

mcp = FastMCP("monday-boards-server")


class MondayAPIError(RuntimeError):
    pass


def _require_token(api_token: str | None = None) -> str:
    token = api_token or os.getenv("MONDAY_API_TOKEN")
    if not token:
        raise MondayAPIError(
            "MONDAY_API_TOKEN is missing. Set it in your environment before running."
        )
    return token


def _post_graphql(
    query: str,
    variables: dict[str, Any],
    api_token: str | None = None,
) -> dict[str, Any]:
    headers = {
        "Authorization": _require_token(api_token),
        "Content-Type": "application/json",
    }
    response = requests.post(
        MONDAY_API_URL,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise MondayAPIError(f"monday.com GraphQL errors: {payload['errors']}")
    data = payload.get("data")
    if data is None:
        raise MondayAPIError("monday.com response did not include a 'data' object.")
    return data


@mcp.tool
def get_all_boards(
    limit_per_page: int = 100,
    api_token: str | None = None,
) -> dict[str, Any]:
    """
    Fetch all monday.com boards (auto-paginated) including board-level column metadata.
    """
    if limit_per_page < 1 or limit_per_page > 100:
        raise ValueError("limit_per_page must be between 1 and 100.")

    query = """
    query ($limit: Int!, $page: Int!) {
      boards(limit: $limit, page: $page) {
        id
        name
        description
        state
        board_kind
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
    page = 1

    while True:
        data = _post_graphql(
            query=query,
            variables={"limit": limit_per_page, "page": page},
            api_token=api_token,
        )
        boards = data.get("boards", [])
        if not boards:
            break
        all_boards.extend(boards)
        if len(boards) < limit_per_page:
            break
        page += 1

    return {
        "count": len(all_boards),
        "boards": all_boards,
    }


if __name__ == "__main__":
    mcp.run()
