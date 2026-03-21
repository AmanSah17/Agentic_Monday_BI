from __future__ import annotations

from typing import Any

from founder_bi_agent.backend.config import AgentSettings
from founder_bi_agent.backend.llm.fallback_insight import generate_insight_from_data


class GeminiSQLPlanner:
    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self._clients: dict[str, Any] = {}
        self.last_generation_meta: dict[str, Any] = {
            "provider": settings.llm_provider,
            "mode": "uninitialized",
        }

    def _create_client(self, model: str) -> Any:
        if not self.settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set.")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise RuntimeError(
                "Install langchain-google-genai to use Gemini."
            ) from exc
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=self.settings.google_api_key,
            temperature=0,
            max_retries=0,
            timeout=20,
        )

    def _get_client(self, model: str) -> Any:
        if model not in self._clients:
            self._clients[model] = self._create_client(model)
        return self._clients[model]

    def _candidate_models(self) -> list[str]:
        ordered = [self.settings.llm_sql_model, *self.settings.llm_sql_model_variants]
        out: list[str] = []
        seen: set[str] = set()
        for model in ordered:
            name = str(model).strip()
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
        if self.settings.llm_provider != "gemini":
            self.last_generation_meta = {
                "provider": self.settings.llm_provider,
                "mode": "fallback_non_gemini_provider",
            }
            return fallback_sql

        failures: list[dict[str, str]] = []
        candidates = self._candidate_models()

        try:
            prompt = (
                "You are a strict analytics SQL assistant for DuckDB.\n"
                "Return only one read-only SQL query.\n"
                "Use only existing tables/columns in schema.\n"
                "No markdown fences.\n\n"
                f"Schema:\n{schema_hint}\n\n"
                f"Question:\n{question}\n"
            )

            for model in candidates:
                try:
                    client = self._get_client(model)
                    response = client.invoke(prompt)
                    sql_text = getattr(response, "content", "") or ""
                    sql_text = str(sql_text).strip()
                    if not sql_text:
                        failures.append({"model": model, "error": "empty_sql_output"})
                        continue
                    self.last_generation_meta = {
                        "provider": "gemini",
                        "mode": "llm_sql_generated",
                        "model": model,
                        "attempted_models": candidates,
                        "failures_before_success": failures,
                    }
                    return sql_text
                except Exception as model_exc:
                    error_text = str(model_exc)
                    failures.append({"model": model, "error": error_text})
                    upper = error_text.upper()
                    # if "RESOURCE_EXHAUSTED" in upper or "QUOTA" in upper or "429" in upper:
                    #     break
                    continue

            self.last_generation_meta = {
                "provider": "gemini",
                "mode": "fallback_all_models_failed",
                "attempted_models": candidates,
                "errors": failures,
            }
            return fallback_sql
        except Exception as exc:
            self.last_generation_meta = {
                "provider": "gemini",
                "mode": "fallback_exception",
                "error": str(exc),
                "attempted_models": candidates,
                "errors": failures,
            }
            return fallback_sql

class GeminiFoundationClient:
    """
    Foundation reasoning client using Gemini.
    Handles semantic routing, clarification, and insight writing.
    """

    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self._clients: dict[str, Any] = {}

    def _create_client(self, model: str) -> Any:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise RuntimeError(
                "Install langchain-google-genai to use Gemini foundation client."
            ) from exc

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=self.settings.google_api_key,
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
            getattr(self.settings, "llm_reasoning_model", "gemini-2.5-pro"),
            *getattr(self.settings, "llm_reasoning_model_variants", []),
            "gemini-2.0-flash",
            "gemini-2.5-pro",
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
            getattr(self.settings, "llm_insight_model", "gemini-2.0-flash"),
            *getattr(self.settings, "llm_insight_model_variants", []),
            "gemini-2.0-flash",
            "gemini-2.5-pro",
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
            "Respond ONLY with the intent string (e.g., 'pipeline_health' or 'general_bi') and nothing else."
        )
        for model in self._candidate_models():
            try:
                client = self._get_client(model)
                response = client.invoke(prompt)
                intent = str(getattr(response, "content", "")).strip().lower()
                if intent in {"pipeline_health", "general_bi"}:
                    return intent
            except Exception:
                continue
        return "general_bi"

    def clarify(self, question: str, intent: str, conversation_history: list[dict[str, str]] | None = None) -> tuple[bool, str]:
        # Build conversation context
        history_context = ""
        if conversation_history:
            history_lines = []
            for msg in conversation_history:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "").strip()
                if content and len(content) < 500:
                    history_lines.append(f"{role}: {content}")
            if history_lines:
                history_context = "\n".join(history_lines[-6:])
        
        prompt = (
            "You are a helpful BI assistant determining if a user's question needs clarification.\n"
            "CRITICAL RULE: Check if information (sector, timeframe, or other details) has ALREADY been provided in prior conversation turns.\n"
            "If yes, DON'T ask again. Only ask for NEW or missing information.\n\n"
            f"Prior Conversation:\n{history_context or '(No prior context)'}\n\n"
            f"Current Question: {question}\n\n"
            "Return a JSON object with two fields:\n"
            "- 'needs_clarification' (boolean)\n"
            "- 'clarification_question' (string, empty if none needed or info already provided, otherwise ask ONE specific new question)\n\n"
            "Respond ONLY with JSON."
        )
        for model in self._candidate_models():
            try:
                client = self._get_client(model)
                response = client.invoke(prompt)
                content = str(getattr(response, "content", "")).strip()
                
                import json
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                
                data = json.loads(content.strip())
                return bool(data.get("needs_clarification")), str(data.get("clarification_question", ""))
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

        data_preview = ""
        if result_df is not None and not result_df.empty:
            data_preview = result_df.head(5).to_markdown()
        else:
            data_preview = "No rows returned."

        prompt = (
            "You are a business intelligence analyst writing a concise final insight for the founder.\n"
            f"Question: {question}\n\n"
            f"SQL Execution Error (if any): {sql_execution_error or 'None'}\n\n"
            f"Data Preview (Top 5 rows):\n{data_preview}\n\n"
            "Instructions:\n"
            "1. Answer the question directly using the data preview.\n"
            "2. If no data was returned, state that.\n"
            "3. If there was an SQL error, state that a fallback query was used.\n"
            "4. Be very concise, professional, and do not repeat the data preview in table format, just summarize the insight."
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
        
        # Fallback: Use data-driven insight generator when LLM unavailable
        import pandas as pd
        try:
            return generate_insight_from_data(question, result_df, sql_execution_error)
        except Exception:
            # Final fallback if even simple insight generation fails
            return f"Query executed successfully and returned {len(result_df) if result_df is not None and not result_df.empty else 0} results. LLM insight generation unavailable, but data retrieval was successful."
