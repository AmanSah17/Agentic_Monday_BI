from __future__ import annotations

from typing import Any

from founder_bi_agent.backend.config import AgentSettings


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
            "gemini-3.1-flash",
            "gemini-3-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash", 
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro", 
            "gemini-1.5-flash",
            "gemini-pro"
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

    def clarify(self, question: str, intent: str) -> tuple[bool, str]:
        prompt = (
            "You are a helpful BI assistant determining if a user's question needs clarification regarding timeframes.\n"
            "If the question talks about performance, pipeline, or trends but lacks a specific time period (e.g., this quarter, last month, Q1), "
            "it needs clarification. If a time period is implied or explicitly stated, it does NOT need clarification.\n\n"
            f"Question: {question}\n\n"
            "Return a JSON object with two fields:\n"
            "- 'needs_clarification' (boolean)\n"
            "- 'clarification_question' (string, empty if none needed, "
            "otherwise ask which timeframe they prefer, such as 'this quarter', 'last month', etc.)\n\n"
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
        if "column names" in question.lower() or "dataset" in question.lower():
            return (
                "This dataset is a business operations + revenue intelligence model built from two monday boards. "
                "The Deals board captures pipeline creation, stage movement, close-date expectation, sector/service and masked deal value. "
                "The Work Orders board captures execution lifecycle, billing/collection progression, receivables and delivery milestones. "
                "Together they support founder-level questions across pipeline health, conversion and cash-flow realization. "
                f"Current inferred schema size: deals={len(table_schemas.get('deals', []))} columns, "
                f"work_orders={len(table_schemas.get('work_orders', []))} columns."
            )
            
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
        for model in self._candidate_models():
            try:
                client = self._get_client(model)
                response = client.invoke(prompt)
                return str(getattr(response, "content", "")).strip()
            except Exception as e:
                last_error = str(e)
                continue
                
        fallback = "I ran a live analysis but encountered an error generating the final insight summary across all models: " + last_error
        return fallback
