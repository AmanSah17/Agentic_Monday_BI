from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

from founder_bi_agent.backend.core.config import AgentSettings
from founder_bi_agent.backend.graph.workflow import build_graph
from founder_bi_agent.backend.sql.duckdb_engine import DuckDBSession
from founder_bi_agent.backend.tools.monday_bi_tools import MondayBITools


def setup_env(settings: AgentSettings) -> None:
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_TRACING"] = "true" if settings.langsmith_tracing else "false"
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project


class FounderBIService:
    def __init__(self) -> None:
        self._load_env_files()
        self.settings = AgentSettings.from_env()
        setup_env(self.settings)
        self.app = build_graph(self.settings)

    @staticmethod
    def _load_env_files() -> None:
        """
        Load env robustly regardless of process working directory.
        Priority:
        1) CWD .env
        2) project root .env (two levels up from backend/)
        3) founder_bi_agent/.env
        """
        cwd_env = Path.cwd() / ".env"
        project_root_env = Path(__file__).resolve().parents[2] / ".env"
        package_env = Path(__file__).resolve().parents[1] / ".env"

        for env_path in [cwd_env, project_root_env, package_env]:
            if env_path.exists():
                load_dotenv(dotenv_path=env_path, override=False)

    def run_query(
        self,
        question: str,
        session_id: str = "default_session",
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        initial_state: dict[str, Any] = {
            "session_id": session_id,
            "question": question,
            "conversation_history": conversation_history or [],
            "traces": [],
        }
        state = self.app.invoke(initial_state)

        result_df = state.get("result_df")
        if isinstance(result_df, pd.DataFrame):
            result_records = result_df.to_dict(orient="records")
        else:
            result_records = []

        return {
            "answer": state.get("answer", ""),
            "needs_clarification": state.get("needs_clarification", False),
            "clarification_question": state.get("clarification_question"),
            "sql_query": state.get("sql_query"),
            "sql_validation_error": state.get("sql_validation_error"),
            "result_records": result_records,
            "chart_spec": state.get("chart_spec", {}),
            "quality_report": state.get("quality_report", {}),
            "board_map": state.get("board_map", {}),
            "board_schemas": state.get("board_schemas", []),
            "table_schemas": state.get("table_schemas", {}),
            "last_result_summary": state.get("last_result_summary", ""),
            "traces": state.get("traces", []),
        }

    def execute_sql_query(self, sql: str) -> pd.DataFrame:
        """
        Execute a raw SQL query against the live Monday.com data.
        """
        tools = MondayBITools(self.settings)
        tables = self.settings.monday_mode
        client = tools.client
        tables = client.fetch_relevant_tables()
        db = DuckDBSession()
        db.register_tables(tables)
        return db.query(sql)

    def execute_dashboard_queries(self, queries: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
        """
        Executes a batch of SQL queries using a single data fetch and DuckDB session.
        Drastically reduces latency by avoiding redundant API calls.
        """
        tools = MondayBITools(self.settings)
        client = tools.client
        tables = client.fetch_relevant_tables()
        db = DuckDBSession()
        db.register_tables(tables)
        
        results = {}
        from founder_bi_agent.backend.api import _sanitize_for_json
        for key, sql in queries.items():
            df = db.query(sql)
            # Optimize to dict and serialize nulls cleanly
            results[key] = [_sanitize_for_json(row.to_dict()) for _, row in df.iterrows()]
        return results


def run_founder_query(
    question: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    service = FounderBIService()
    return service.run_query(question, conversation_history=conversation_history)
