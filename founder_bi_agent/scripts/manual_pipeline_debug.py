from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from founder_bi_agent.backend.service import FounderBIService


DEFAULT_QUERIES = [
    "How is our pipeline by sector this quarter?",
    "Show deal count by deal stage.",
    "What is the total amount receivable in work orders?",
    "Compare billed vs collected amounts in work orders by sector.",
    "How's our pipeline looking?",  # expects clarification
]


def summarize_response(question: str, response: dict[str, Any]) -> dict[str, Any]:
    traces = response.get("traces", [])
    planner_trace = next((t for t in traces if t.get("node") == "text2sql_planner"), {})
    data_fetch_trace = next((t for t in traces if t.get("node") == "data_fetch_live"), {})
    sql_preview = (response.get("sql_query") or "").strip().replace("\n", " ")
    return {
        "question": question,
        "needs_clarification": response.get("needs_clarification"),
        "clarification_question": response.get("clarification_question"),
        "row_count": len(response.get("result_records", [])),
        "sql_preview": sql_preview[:250],
        "planner_meta": (planner_trace.get("details") or {}).get("planner_meta"),
        "board_map": response.get("board_map"),
        "tool_trace_count": len((data_fetch_trace.get("details") or {}).get("tool_trace", [])),
        "answer_preview": str(response.get("answer", ""))[:260],
    }


def main() -> None:
    service = FounderBIService()
    history: list[dict[str, str]] = []
    detailed_results: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []

    for idx, question in enumerate(DEFAULT_QUERIES, start=1):
        print(f"\n[{idx}/{len(DEFAULT_QUERIES)}] Query: {question}")
        response = service.run_query(question, conversation_history=history)
        detailed_results.append({"question": question, "response": response})
        summary = summarize_response(question, response)
        summary_rows.append(summary)
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": response.get("answer", "")})
        print(json.dumps(summary, ensure_ascii=True, indent=2))

    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(__file__).resolve().parents[1] / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    detailed_path = out_dir / f"manual_debug_detailed_{ts}.json"
    summary_path = out_dir / f"manual_debug_summary_{ts}.json"

    with detailed_path.open("w", encoding="utf-8") as f:
        json.dump(detailed_results, f, ensure_ascii=True, default=str, indent=2)
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary_rows, f, ensure_ascii=True, default=str, indent=2)

    print(f"\nSaved detailed debug report: {detailed_path}")
    print(f"Saved summary debug report: {summary_path}")


if __name__ == "__main__":
    main()
