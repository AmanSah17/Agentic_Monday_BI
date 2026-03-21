from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from founder_bi_agent.backend.config import AgentSettings
from founder_bi_agent.backend.sql.sql_planner import build_schema_hint, generate_sql_heuristic
from founder_bi_agent.backend.llm.sql_prompt_context import SYSTEM_PROMPT_SQL_GENERATION, create_validation_hint
from founder_bi_agent.backend.llm.foundation_prompts import (
    SYSTEM_PROMPT_INSIGHT_GENERATION,
    SYSTEM_PROMPT_INTENT_CLASSIFICATION,
    SYSTEM_PROMPT_CLARIFICATION_EXPERT,
)

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
            api_base=self.settings.groq_base_url,
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

    def _candidate_models_for_insight(self) -> list[str]:
        """Models optimized for summarization and business insight generation"""
        ordered = [
            getattr(self.settings, "llm_insight_model", "llama-3.1-70b-versatile"),
            "llama-3.3-70b-versatile",
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
        prompt = SYSTEM_PROMPT_INTENT_CLASSIFICATION + f"\n\nUser Question: {question}\n\nRespond with the primary INTENT classification ONLY (PIPELINE_HEALTH, REVENUE_PERFORMANCE, EXECUTION_HEALTH, CONVERSION_ANALYSIS, TEAM_PERFORMANCE, SECTOR_ANALYSIS, BOTTLENECK_DISCOVERY, RISK_ASSESSMENT, or FORECASTING)."
        for model in self._candidate_models():
            try:
                client = self._get_client(model)
                response = client.invoke(prompt)
                intent = str(getattr(response, "content", "")).strip().lower()
                if "pipeline_health" in intent: return "pipeline_health"
                if "revenue_performance" in intent: return "revenue_performance"
                if "general_bi" in intent: return "general_bi"
            except Exception:
                continue
        return "general_bi"

    def clarify(self, question: str, intent: str, conversation_history: list[dict[str, str]] | None = None) -> tuple[bool, str]:
        """
        Determine if clarification is needed based on current question and conversation history.
        
        If information (sector, timeframe, etc.) has already been provided in previous turns,
        DON'T ask for it again. Only ask for truly missing critical information.
        """
        # Build conversation context
        history_context = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "").strip()
                if content and len(content) < 500:  # Skip very long messages
                    history_lines.append(f"{role}: {content}")
            if history_lines:
                history_context = "\n".join(history_lines[-6:])  # Last 6 turns for context
        
        prompt = (
            SYSTEM_PROMPT_CLARIFICATION_EXPERT +
            f"\n\nConversation History:\n{history_context or '(No prior context)'}\n\n"
            f"Current Question: {question}\n"
            f"Identified Intent: {intent}\n\n"
            "Task: Determine if clarification is needed.\n"
            "CRITICAL: Check if information (sector, time period, details) has ALREADY been provided in conversation history.\n"
            "If yes, DON'T ask again. Only ask for NEW or missing critical information.\n"
            "If no clarification needed, respond: 'No clarification needed - ready to analyze'"
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
        """
        Generate executive-grade business insights using dedicated insight model.
        Uses LLM_INSIGHT_MODEL to prioritize summarization and analysis quality.
        """
        data_preview = "No rows returned."
        if result_df is not None and not result_df.empty:
            data_preview = result_df.head(10).to_markdown()

        prompt = (
            SYSTEM_PROMPT_INSIGHT_GENERATION +
            f"\n\nExecutive Question: {question}\n\n"
            f"Query Execution Metadata:\n"
            f"- SQL Error (if any): {sql_execution_error or 'None'}\n"
            f"- Data Quality: {quality_report}\n\n"
            f"Query Results (Data Preview):\n{data_preview}\n\n"
            "Task: Transform this raw data into an executive insight following the structure:"
            "1. HEADLINE (1 sentence answer)\n"
            "2. KEY METRICS (most important numbers)\n"
            "3. ANALYSIS (so what? business meaning)\n"
            "4. RISKS & OPPORTUNITIES\n"
            "5. RECOMMENDED ACTIONS\n"
            "\nUse the tone and style specified in your system prompt. Be confident, quantitative, actionable."
        )
        
        last_error = ""
        for model in self._candidate_models_for_insight():
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
            api_base=self.settings.groq_base_url,
            temperature=0.0,
            max_retries=1,
            timeout=30,
        )

    def _get_client(self, model: str) -> Any:
        if model not in self._clients:
            self._clients[model] = self._create_client(model)
        return self._clients[model]

    def _candidate_models(self) -> list[str]:
        """SQL generation models optimized for code/SQL translation"""
        ordered = [
            getattr(self.settings, "llm_sql_model", "qwen-2.5-coder-32b"),
        ]
        # Add variants if configured
        variants = getattr(self.settings, "llm_sql_model_variants", [])
        if variants:
            ordered.extend(variants)
        else:
            ordered.extend(["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
        
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
        schema_hint: str,
        fallback_sql: str,
    ) -> str:
        """
        Translate natural language to SQL using Groq's high-speed endpoints.
        
        Args:
            question: User's natural language query
            schema_hint: Pre-built schema metadata (already formatted)
            fallback_sql: Pre-computed heuristic SQL to return on failure
        
        Returns:
            Valid DuckDB SQL string
        """
        
        prompt = (
            SYSTEM_PROMPT_SQL_GENERATION + "\n\n"
            "SCHEMA DEFINITION:\n"
            f"{schema_hint}\n\n"
            f"USER QUESTION: {question}\n\n"
            "ADDITIONAL VALIDATION:\n"
            f"{create_validation_hint()}"
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
                    "mode": "llm_sql_generated",
                    "used_model": model,
                    "attempted_models": candidates[: candidates.index(model) + 1],
                    "failures_before_success": failures,
                }
                return sql.strip()
            except Exception as model_exc:
                error_text = str(model_exc)
                failures.append({"model": model, "error": error_text})
                continue

        # All models failed; return fallback
        self.last_generation_meta = {
            "provider": "groq",
            "mode": "fallback_heuristic",
            "reason": "all_groq_models_exhausted",
            "attempted_models": candidates,
            "errors": failures,
        }
        return fallback_sql
