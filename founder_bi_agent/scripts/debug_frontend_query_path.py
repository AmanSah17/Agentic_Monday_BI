from __future__ import annotations

import json
import requests


def run() -> None:
    session_id = "frontend-debug-session"
    payload = {
        "question": "How many tables are connected and what are their row counts?",
        "conversation_history": [],
        "session_id": session_id,
    }
    response = requests.post(
        "http://127.0.0.1:8010/query",
        json=payload,
        timeout=240,
    )
    print("status_code:", response.status_code)
    print("content_type:", response.headers.get("content-type"))
    if response.status_code != 200:
        print(response.text)
        return
    data = response.json()
    print("session_id:", data.get("session_id"))
    print("history_backend:", data.get("history_backend"))
    print("conversation_history_length:", data.get("conversation_history_length"))
    print("sql_query:", data.get("sql_query"))
    print("result_rows:", len(data.get("result_records", [])))
    print("trace_nodes:", [t.get("node") for t in data.get("traces", [])])
    print("\nanswer_preview:\n", (data.get("answer", "") or "")[:300])
    print("\nfirst_result_row:\n", json.dumps((data.get("result_records") or [{}])[0], indent=2))


if __name__ == "__main__":
    run()
