from __future__ import annotations

from typing import Any, TypedDict

import pandas as pd


class BIState(TypedDict, total=False):
    question: str
    conversation_history: list[dict[str, str]]
    intent: str
    needs_clarification: bool
    clarification_question: str
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
    answer: str
    chart_spec: dict[str, Any]
    traces: list[dict[str, Any]]
