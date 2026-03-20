from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from founder_bi_agent.backend.config import AgentSettings
from founder_bi_agent.backend.sql.sql_planner import build_schema_hint, generate_sql_heuristic

class ClarificationOutput(BaseModel):
    needs_clarification: bool = Field(description="Whether the original question requires timeframe or detail clarification.")
    clarification_question: str = Field(default="", description="The question generated to ask the user for clarification.")


class GroqFoundationClient:
    """
    Foundation reasoning client using Groq's high-speed LPU API.
    Handles semantic routing, clarification, and insight writing.
    Defaults to Llama-3.3-70b for dense reasoning logic.
    """

    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self._clients: dict[str, Any] = {}

    def _create_client(self, model: str) -> Any:
        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:
            raise RuntimeError("Install langchain-groq to use Groq foundation client.") from exc

        return ChatGroq(
            model=model,
            api_key=self.settings.groq_api_key,
            temperature=0.1,
            max_retries=1,
            timeout=30,
        )

    def _get_client(self, model: str) -> Any:
        if model not in self._clients:
            self._clients[model] = self._create_client(model)
        return self._clients[model]

    def _candidate_models(self) -> list[str]:
        ordered = [
            getattr(self.settings, "llm_reasoning_model", "llama-3.3-70b-versatile"),
            "qwen-2.5-coder-32b",
            "mixtral-8x7b-32768",
            "llama-3.1-8b-instant"
        ]
        out: list[str] = []
        seen: set[str] = set()
        for m in ordered:
            name = str(m).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            out.append(name)
        return out

    def route_intent(self, question: str) -> str:
        prompt = (
            "You are an intent router for a Monday.com BI Agent.\n"
            "Classify the user's question into exactly one of these intents:\n"
            "- 'pipeline_health': queries related to deal funnel, pipeline value, deal stages, or sales.\n"
            "- 'general_bi': queries related to work orders, billing, receivables, collections, or general operations.\n\n"
            f"Question: {question}\n\n"
            "Respond ONLY with the exact intent string ('pipeline_health' or 'general_bi')."
        )
        for model in self._candidate_models():
            try:
                client = self._get_client(model)
                response = client.invoke(prompt)
                intent = str(getattr(response, "content", "")).strip().lower()
                if "pipeline_health" in intent: return "pipeline_health"
                if "general_bi" in intent: return "general_bi"
            except Exception:
                continue
        return "general_bi"

    def clarify(self, question: str, intent: str) -> tuple[bool, str]:
        prompt = (
            "You are a helpful BI assistant determining if a user's question needs clarification regarding timeframes.\n"
            "If the question evaluates performance, pipeline, or trends but lacks a specific time period (e.g., this quarter, last month, Q1), "
            "it needs clarification. If a time period is implied or stated, or it is a static question, it does NOT need clarification.\n\n"
            f"Question: {question}\n"
        )
        for model in self._candidate_models():
            try:
                client = self._get_client(model)
                structured_client = client.with_structured_output(ClarificationOutput)
                response = structured_client.invoke(prompt)
                return bool(response.needs_clarification), str(response.clarification_question)
            except Exception:
                continue
        return False, ""

    def write_insight(
        self,
        question: str,
        result_df: Any,
        quality_report: dict[str, Any],
        table_schemas: dict[str, Any],
        sql_execution_error: str | None,
    ) -> str:
        data_preview = "No rows returned."
        if result_df is not None and not result_df.empty:
            data_preview = result_df.head(5).to_markdown()

        prompt = (
            "You are a business intelligence analyst writing a concise final insight for an executive.\n"
            f"Question: {question}\n\n"
            f"SQL Execution Error (if any): {sql_execution_error or 'None'}\n\n"
            f"Data Preview (Top 5 rows):\n{data_preview}\n\n"
            "Instructions:\n"
            "1. Answer the question directly using the data preview.\n"
            "2. If no data was returned, state that.\n"
            "3. If there was an SQL error, state that a fallback generic query was used.\n"
            "4. Be very concise, professional, and do not copy the data preview markdown table inside your response."
        )
        
        last_error = ""
        for model in self._candidate_models():
            try:
                client = self._get_client(model)
                response = client.invoke(prompt)
                return str(getattr(response, "content", "")).strip()
            except Exception as e:
                last_error = str(e)
                continue
                
        return "I ran a live analysis but encountered an error generating the final insight summary across all Groq models: " + last_error


class GroqSQLPlanner:
    """
    Translates natural language to SQL using Groq's high-speed endpoints.
    Prioritizes models like Llama-3.3-70b or Qwen-2.5-Coder for reliable SQL logic.
    """

    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.last_generation_meta: dict[str, Any] = {}
        self._clients: dict[str, Any] = {}

    def _create_client(self, model: str) -> Any:
        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:
            raise RuntimeError("Install langchain-groq to use Groq NLP-to-SQL functionality.") from exc

        return ChatGroq(
            model=model,
            api_key=self.settings.groq_api_key,
            temperature=0.0,
            max_retries=1,
            timeout=30,
        )

    def _get_client(self, model: str) -> Any:
        if model not in self._clients:
            self._clients[model] = self._create_client(model)
        return self._clients[model]

    def _candidate_models(self) -> list[str]:
        ordered = [
            getattr(self.settings, "llm_sql_model", "qwen-2.5-coder-32b"),
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ]
        out: list[str] = []
        seen: set[str] = set()
        for m in ordered:
            name = str(m).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            out.append(name)
        return out

    def generate_sql(
        self,
        question: str,
        tables: dict[str, pd.DataFrame],
        schema_hint: str = "",
        history: list[dict[str, str]] | None = None,
    ) -> str:
        if not schema_hint:
            schema_hint = build_schema_hint(tables)
            
        fallback_sql = generate_sql_heuristic(question, tables)
        
        prompt = (
            "You are an expert DuckDB SQL data analyst. You write advanced analytical queries based on provided schemas.\n\n"
            "SCHEMA DEFINITION:\n"
            f"{schema_hint}\n\n"
            f"USER QUESTION: {question}\n\n"
            "INSTRUCTIONS:\n"
            "- Return strictly valid DuckDB SQL.\n"
            "- Do NOT wrap the SQL in markdown blocks (e.g., no ```sql). Just return the raw SQL string.\n"
            "- Use 'deals' or 'work_orders' as the main table names where appropriate.\n"
            "- Handle date columns by casting or extracting carefully if required.\n"
        )
        
        candidates = self._candidate_models()
        failures = []
        
        for model in candidates:
            try:
                client = self._get_client(model)
                response = client.invoke([
                    SystemMessage(content=prompt),
                    HumanMessage(content=question)
                ])
                sql = str(getattr(response, "content", "")).strip()
                if sql.startswith("```sql"): sql = sql[6:]
                if sql.startswith("```"): sql = sql[3:]
                if sql.endswith("```"): sql = sql[:-3]
                
                self.last_generation_meta = {
                    "provider": "groq",
                    "mode": "success",
                    "used_model": model,
                    "attempted_models": candidates[: candidates.index(model) + 1],
                    "errors": failures,
                }
                return sql.strip()
            except Exception as model_exc:
                error_text = str(model_exc)
                failures.append({"model": model, "error": error_text})
                continue

        self.last_generation_meta = {
            "provider": "groq",
            "mode": "fallback_exception",
            "error": failures[-1]["error"] if failures else "Unknown",
            "attempted_models": candidates,
            "errors": failures,
        }
        return fallback_sql
