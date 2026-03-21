from __future__ import annotations

from typing import Any, TypedDict

import pandas as pd


class BIState(TypedDict, total=False):
    session_id: str
    question: str
    conversation_history: list[dict[str, str]]
    long_term_context: str
    intent: str
    needs_clarification: bool
    clarification_question: str
    needs_web_search: bool
    search_query: str
    reflection_retry: bool
    board_map: dict[str, Any]
    board_schemas: list[dict[str, Any]]
    table_schemas: dict[str, list[dict[str, Any]]]
    raw_tables: dict[str, pd.DataFrame]
    cleaned_tables: dict[str, pd.DataFrame]
    quality_report: dict[str, Any]
    sql_query: str
    fallback_sql_query: str
    sql_validation_error: str | None
    sql_execution_error: str | None
    result_df: pd.DataFrame
    last_result_summary: str
    answer: str
    chart_spec: dict[str, Any]
    web_research_results: list[dict[str, Any]]
    traces: list[dict[str, Any]]
