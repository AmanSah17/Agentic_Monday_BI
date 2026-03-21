from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from concurrent.futures import ThreadPoolExecutor

from founder_bi_agent.backend.config import AgentSettings
from founder_bi_agent.backend.llm.google_gemini import GeminiSQLPlanner, GeminiFoundationClient
from founder_bi_agent.backend.llm.qwen_sql import QwenSQLPlanner
from founder_bi_agent.backend.llm.vllm_openai import VLLMSQLPlanner
from founder_bi_agent.backend.llm.zhipuai_client import GLMFoundationClient
from founder_bi_agent.backend.llm.groq_client import GroqFoundationClient, GroqSQLPlanner
from founder_bi_agent.backend.sql.duckdb_engine import DuckDBSession
from founder_bi_agent.backend.sql.duckdb_engine import DuckDBSession
from founder_bi_agent.backend.sql.sql_guardrails import validate_read_only_sql
from founder_bi_agent.backend.sql.sql_planner import build_schema_hint, generate_sql_heuristic
from founder_bi_agent.backend.tools.monday_bi_tools import MondayBITools
from founder_bi_agent.backend.tools.web_research_tools import WebResearchTools
from founder_bi_agent.backend.llm.huggingface_client import HuggingFaceClient


def _append_trace(state: dict[str, Any], node: str, details: dict[str, Any]) -> list[dict[str, Any]]:
    traces = list(state.get("traces", []))
    traces.append(
        {
            "ts": datetime.utcnow().isoformat() + "Z",
            "node": node,
            "details": details,
        }
    )
    return traces


class FounderBINodes:
    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.monday_tools = MondayBITools(settings)
        self.web_tools = WebResearchTools(settings)
        self.executive_brain = HuggingFaceClient(settings)
        if settings.llm_provider == "groq":
            self.foundation_llm = GroqFoundationClient(settings)
            self.sql_planner = GroqSQLPlanner(settings)
        elif settings.llm_provider == "gemini":
            self.foundation_llm = GeminiFoundationClient(settings)
            self.sql_planner = GeminiSQLPlanner(settings)
        elif settings.llm_provider in {"vllm", "openai_compat", "openai", "huggingface"}:
            self.foundation_llm = GLMFoundationClient(settings)
            self.sql_planner = VLLMSQLPlanner(settings)
        elif settings.llm_provider == "qwen":
            self.foundation_llm = GLMFoundationClient(settings)
            self.sql_planner = QwenSQLPlanner(settings)
        else:
            self.foundation_llm = GLMFoundationClient(settings)
            self.sql_planner = None

    def intent_router(self, state: dict[str, Any]) -> dict[str, Any]:
        question = state["question"]
        intent = self.foundation_llm.route_intent(question)
        return {
            "intent": intent,
            "traces": _append_trace(
                state,
                "intent_router",
                {"intent": intent},
            ),
        }

    def clarifier(self, state: dict[str, Any]) -> dict[str, Any]:
        question = state["question"]
        intent = state.get("intent", "general_bi")
        conversation_history = state.get("conversation_history", [])
        needs_clarif, clarif_q = self.foundation_llm.clarify(question, intent, conversation_history)
        return {
            "needs_clarification": needs_clarif,
            "clarification_question": clarif_q,
            "traces": _append_trace(
                state,
                "clarifier",
                {"needs_clarification": needs_clarif, "q": clarif_q, "context_turns": len(conversation_history)},
            ),
        }

    def schema_discovery(self, state: dict[str, Any]) -> dict[str, Any]:
        all_boards = self.monday_tools.list_boards()
        board_map = self.monday_tools.discover_bi_boards(boards=all_boards)
        deals_schema = self.monday_tools.get_board_schema(
            board_id=board_map["deals"].board_id,
            boards=all_boards,
        )
        work_orders_schema = self.monday_tools.get_board_schema(
            board_id=board_map["work_orders"].board_id,
            boards=all_boards,
        )
        board_schemas = [deals_schema, work_orders_schema]
        tool_trace = self.monday_tools.pop_trace()
        return {
            "board_schemas": board_schemas,
            "board_map": {
                "deals": {
                    "board_id": board_map["deals"].board_id,
                    "board_name": board_map["deals"].board_name,
                },
                "work_orders": {
                    "board_id": board_map["work_orders"].board_id,
                    "board_name": board_map["work_orders"].board_name,
                },
            },
            "traces": _append_trace(
                state,
                "schema_discovery",
                {
                    "board_count": len(board_schemas),
                    "strict_board_names": [
                        self.settings.monday_deals_board_name,
                        self.settings.monday_work_orders_board_name,
                    ],
                    "tool_trace": tool_trace,
                },
            ),
        }

    def data_fetch_live(self, state: dict[str, Any]) -> dict[str, Any]:
        board_map: dict[str, Any] = state.get("board_map", {})
        board_schemas: list[dict[str, Any]] = state.get("board_schemas", [])

        deals_meta = board_map.get("deals") or {}
        work_orders_meta = board_map.get("work_orders") or {}
        deals_board_id = int(deals_meta["board_id"])
        work_orders_board_id = int(work_orders_meta["board_id"])

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_deals = executor.submit(self.monday_tools.fetch_board_table, deals_board_id)
            future_wo = executor.submit(self.monday_tools.fetch_board_table, work_orders_board_id)
            deals_df = future_deals.result()
            work_orders_df = future_wo.result()

        deals_board_schema = next(
            (x for x in board_schemas if int(x.get("id", 0)) == deals_board_id),
            {},
        )
        work_orders_board_schema = next(
            (x for x in board_schemas if int(x.get("id", 0)) == work_orders_board_id),
            {},
        )
        tables = {"deals": deals_df, "work_orders": work_orders_df}
        table_schemas = {
            "deals": self.monday_tools.infer_table_schema(deals_df, "deals"),
            "work_orders": self.monday_tools.infer_table_schema(work_orders_df, "work_orders"),
        }
        tool_trace = self.monday_tools.pop_trace()
        return {
            "raw_tables": tables,
            "board_schemas": [deals_board_schema, work_orders_board_schema],
            "table_schemas": {
                "deals": table_schemas["deals"].to_dict(orient="records"),
                "work_orders": table_schemas["work_orders"].to_dict(orient="records"),
            },
            "traces": _append_trace(
                state,
                "data_fetch_live",
                {
                    "tables": list(tables.keys()),
                    "row_counts": {k: int(len(v)) for k, v in tables.items()},
                    "tool_trace": tool_trace,
                },
            ),
        }

    def normalize_data(self, state: dict[str, Any]) -> dict[str, Any]:
        raw_tables: dict[str, pd.DataFrame] = state.get("raw_tables", {})
        cleaned: dict[str, pd.DataFrame] = {}

        for table_name, df in raw_tables.items():
            cdf = df.copy()
            cdf.columns = [str(c).strip().lower() for c in cdf.columns]

            for col in cdf.columns:
                if cdf[col].dtype == "object":
                    cdf[col] = cdf[col].astype(str).str.strip()
                    cdf[col] = cdf[col].replace(
                        {"": pd.NA, "none": pd.NA, "null": pd.NA, "nan": pd.NA}
                    )

                if any(tok in col for tok in ["amount", "value", "revenue", "price"]):
                    cdf[col] = (
                        cdf[col]
                        .astype(str)
                        .str.replace(",", "", regex=False)
                        .str.replace("$", "", regex=False)
                    )
                    cdf[col] = pd.to_numeric(cdf[col], errors="coerce")

                if any(tok in col for tok in ["date", "created_at", "updated_at"]):
                    cdf[col] = pd.to_datetime(cdf[col], errors="coerce", format="mixed")

            cleaned[table_name] = cdf

        return {
            "cleaned_tables": cleaned,
            "traces": _append_trace(
                state,
                "normalize_data",
                {"tables_cleaned": list(cleaned.keys())},
            ),
        }

    def quality_profiler(self, state: dict[str, Any]) -> dict[str, Any]:
        cleaned_tables: dict[str, pd.DataFrame] = state.get("cleaned_tables", {})
        report: dict[str, Any] = {}
        for table_name, df in cleaned_tables.items():
            missing = (df.isna().sum() / max(len(df), 1)).round(3).to_dict()
            report[table_name] = {
                "row_count": int(len(df)),
                "column_count": int(len(df.columns)),
                "missing_ratio_by_column": missing,
            }
        return {
            "quality_report": report,
            "traces": _append_trace(
                state,
                "quality_profiler",
                {"tables_profiled": list(cleaned_tables.keys())},
            ),
        }

    def text2sql_planner(self, state: dict[str, Any]) -> dict[str, Any]:
        question = state["question"]
        contextual_question = self._build_contextual_question(state)
        cleaned_tables: dict[str, pd.DataFrame] = state.get("cleaned_tables", {})
        fallback_sql = generate_sql_heuristic(question, cleaned_tables.keys())
        schema_hint = build_schema_hint(cleaned_tables)
        uses_generic_fallback = fallback_sql.strip().lower().startswith("select * from ")

        if not uses_generic_fallback:
            sql_query = fallback_sql
            planner_meta = {
                "provider": self.settings.llm_provider,
                "mode": "heuristic_sql_selected",
            }
        elif self.sql_planner is not None:
            sql_query = self.sql_planner.generate_sql(
                question=contextual_question,
                schema_hint=schema_hint,
                fallback_sql=fallback_sql,
            )
            planner_meta = dict(getattr(self.sql_planner, "last_generation_meta", {}))
        else:
            sql_query = fallback_sql
            planner_meta = {
                "provider": self.settings.llm_provider,
                "mode": "fallback_no_planner_configured",
            }
        return {
            "sql_query": sql_query,
            "fallback_sql_query": fallback_sql,
            "traces": _append_trace(
                state,
                "text2sql_planner",
                {
                    "sql_preview": sql_query[:200],
                    "planner_meta": planner_meta,
                    "contextual_question_preview": contextual_question[:300],
                },
            ),
        }

    def sql_guardrail(self, state: dict[str, Any]) -> dict[str, Any]:
        sql_query = state.get("sql_query", "")
        ok, err = validate_read_only_sql(sql_query)
        return {
            "sql_validation_error": err,
            "traces": _append_trace(
                state,
                "sql_guardrail",
                {"is_valid": ok, "error": err},
            ),
        }

    def sql_execute(self, state: dict[str, Any]) -> dict[str, Any]:
        cleaned_tables: dict[str, pd.DataFrame] = state.get("cleaned_tables", {})
        sql_query = state.get("sql_query", "")
        fallback_sql = state.get("fallback_sql_query", "")
        db = DuckDBSession()
        db.register_tables(cleaned_tables)
        execution_error = None
        used_fallback = False
        try:
            result_df = db.query(sql_query)
        except Exception as exc:
            execution_error = str(exc)
            if fallback_sql and fallback_sql.strip() and fallback_sql.strip() != sql_query.strip():
                result_df = db.query(fallback_sql)
                used_fallback = True
            else:
                raise
        return {
            "result_df": result_df,
            "sql_execution_error": execution_error,
            "sql_query": fallback_sql if used_fallback else sql_query,
            "traces": _append_trace(
                state,
                "sql_execute",
                {
                    "result_rows": int(len(result_df)),
                    "result_columns": list(result_df.columns),
                    "used_fallback_sql": used_fallback,
                    "execution_error": execution_error,
                },
            ),
        }

    def insight_writer(self, state: dict[str, Any]) -> dict[str, Any]:
        result_df: pd.DataFrame = state.get("result_df", pd.DataFrame())
        quality_report = state.get("quality_report", {})
        question = str(state.get("question", "")).lower()
        
        web_results = state.get("web_research_results", [])
        if web_results:
            web_context = "\n\n[CRITICAL WEB Context to synthesize with data]:\n" + "\n".join(f"- {r.get('title', '')}: {r.get('content', '')}" for r in web_results)
            question += web_context
            
        board_schemas = state.get("board_schemas", [])
        table_schemas = state.get("table_schemas", {})
        sql_execution_error = state.get("sql_execution_error")

        answer = self.foundation_llm.write_insight(
            question=question,
            result_df=result_df,
            quality_report=quality_report,
            table_schemas=table_schemas,
            sql_execution_error=sql_execution_error,
        )

        return {
            "answer": answer,
            "traces": _append_trace(
                state,
                "insight_writer",
                {"answer_length": len(answer)},
            ),
        }

    def viz_builder(self, state: dict[str, Any]) -> dict[str, Any]:
        result_df: pd.DataFrame = state.get("result_df", pd.DataFrame())
        chart_spec: dict[str, Any] = {}

        if not result_df.empty and len(result_df.columns) >= 2:
            x_col = str(result_df.columns[0])
            y_col = str(result_df.columns[1])
            if pd.api.types.is_numeric_dtype(result_df[y_col]):
                chart_spec = {
                    "kind": "bar",
                    "x": x_col,
                    "y": y_col,
                    "title": f"{y_col} by {x_col}",
                }

        return {
            "chart_spec": chart_spec,
            "traces": _append_trace(
                state,
                "viz_builder",
                {"has_chart": bool(chart_spec)},
            ),
        }

    @staticmethod
    def _build_contextual_question(state: dict[str, Any]) -> str:
        question = str(state.get("question", ""))
        history = state.get("conversation_history", []) or []
        recent_user_turns = [
            str(turn.get("content", ""))
            for turn in history
            if str(turn.get("role", "")).lower() == "user"
        ][-3:]
        if not recent_user_turns:
            return question
        history_block = "\n".join(f"- {turn}" for turn in recent_user_turns)
        return f"Conversation context:\n{history_block}\n\nCurrent question: {question}"

    def deepseek_executive_planner(self, state: dict[str, Any]) -> dict[str, Any]:
        question = state["question"]
        history = state.get("conversation_history", [])
        needs_search, search_query, reasoning = self.executive_brain.refine_plan(question, history)
        return {
            "needs_web_search": needs_search,
            "search_query": search_query,
            "traces": _append_trace(
                state,
                "deepseek_executive_planner",
                {"needs_search": needs_search, "search_query": search_query, "reasoning": reasoning[:200] + "..."},
            ),
        }

    def web_researcher(self, state: dict[str, Any]) -> dict[str, Any]:
        query = state.get("search_query", "")
        if not query:
            return {"web_research_results": []}
        results = self.web_tools.search_market_trends(query)
        return {
            "web_research_results": results,
            "traces": _append_trace(
                state,
                "web_researcher",
                {"query": query, "results_found": len(results)},
            ),
        }

    def reflection_judge(self, state: dict[str, Any]) -> dict[str, Any]:
        answer = state.get("answer", "")
        # A simple reflection: verify answer is sensible
        needs_retry = False
        if len(answer) < 10 or "error" in answer.lower() or "context skipped" in answer.lower():
            needs_retry = True
            
        return {
            "reflection_retry": needs_retry,
            "traces": _append_trace(
                state,
                "reflection_judge",
                {"needs_retry": needs_retry, "original_answer_len": len(answer)},
            ),
        }

