from google import genai
from typing import Any

from founder_bi_agent.backend.core.config import AgentSettings
from founder_bi_agent.backend.llm.fallback_insight import generate_insight_from_data


class GeminiSQLPlanner:
    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.client = genai.Client(api_key=self.settings.google_api_key)
        self.last_generation_meta: dict[str, Any] = {
            "provider": settings.llm_provider,
            "mode": "uninitialized",
        }

    def _get_client(self, model: str) -> Any:
        # With the new SDK, we mainly use the shared client.
        return self.client

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
            print(f"DEBUG SQL PROMPT:\n{prompt[:1000]}...")

            for model in candidates:
                try:
                    # New SDK generate_content call
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config={"temperature": 0}
                    )
                    sql_text = response.text or ""
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
                    print(f"DEBUG SQL GENERATION ERROR for model {model}: {error_text}")
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
    Foundation reasoning client using Gemini (google-genai SDK).
    """

    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.client = genai.Client(api_key=self.settings.google_api_key)

    def _get_client(self, model: str) -> Any:
        return self.client

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
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"temperature": 0}
                )
                intent = str(response.text or "").strip().lower()
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
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"temperature": 0.1}
                )
                content = str(response.text or "").strip()
                
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
            "You are a Senior Business Intelligence Analyst presenting to a CEO/Founder.\n"
            f"Question: {question}\n\n"
            "AGENT REASONING TRAIL (Steps taken to find this answer):\n"
            f"{question.split('[REASONING TRAIL]:')[1].split('[DATA SUMMARY]:')[0] if '[REASONING TRAIL]:' in question else 'N/A'}\n\n"
            "SYSTEM DATA ANALYSIS:\n"
            f"{question.split('[DATA SUMMARY]:')[1] if '[DATA SUMMARY]:' in question else 'N/A'}\n\n"
            f"SQL Execution Error (if any): {sql_execution_error or 'None'}\n\n"
            f"Data Preview (Top 5 rows for column inspiration):\n{data_preview}\n\n"
            "Instructions:\n"
            "1. **Logical Transparency**: Briefly acknowledge the steps you took (e.g., 'After auditing board schemas and performing a Pareto analysis on 500 records...'). This builds trust with the Founder.\n"
            "2. Synthesize the SYSTEM DATA ANALYSIS into a high-level business narrative.\n"
            "3. **Cross-Table Awareness**: Highlight gaps between Deals (Sales) and Work Orders (Ops).\n"
            "4. Identify the 'Headline Story'.\n"
            "5. **Proactive Follow-ups**: Mandatory section '### Recommended Follow-ups' with 3 data-driven questions.\n"
            "6. Be professional, direct, and slightly provocative."
        )
        
        last_error = ""
        for model in self._candidate_models_for_insight():
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"temperature": 0.2}
                )
                return str(response.text or "").strip()
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

    def refine_plan(self, question: str, history: list[dict[str, str]] = None) -> tuple[bool, str, str]:
        """
        Act as the Executive Brain to determine if web context or deep-dive analysis is needed.
        Returns: (needs_web_search, search_query, internal_reasoning)
        """
        system_prompt = (
            "You are the Executive Brain for Agentic Monday BI. Overlook the user's BI query. "
            "Determine if answering this requires external market context OR a deep-dive statistical analysis of previously retrieved data. "
            "If the user asks for 'in-depth', 'deep dive', or 'analyze the results', prioritize aggregation over simple listing. "
            "Respond in strictly structured format: \n"
            "<think>...your reasoning about whether to search the web or do a deep-dive data analysis...</think>\n"
            "<needs_web_search>true/false</needs_web_search>\n"
            "<search_query>best web search query if needed</search_query>"
        )
        
        history_context = ""
        if history:
            history_lines = []
            for msg in history:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "").strip()
                if content and len(content) < 500:
                    history_lines.append(f"{role}: {content}")
            if history_lines:
                history_context = "\\nPrior Conversation:\\n" + "\\n".join(history_lines)
                
        prompt = f"{system_prompt}\\n{history_context}\\n\\nCurrent Question: {question}"

        for model in self._candidate_models():
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"temperature": 0}
                )
                content = str(response.text or "").strip()
                
                think_tag = content.split("</think>")
                reasoning = think_tag[0].replace("<think>", "").strip() if len(think_tag) > 1 else ""
                
                needs_search = "<needs_web_search>true" in content.lower()
                
                search_query = ""
                if "<search_query>" in content and "</search_query>" in content:
                    search_query = content.split("<search_query>")[1].split("</search_query>")[0].strip()
                    
                return needs_search, search_query, reasoning
            except Exception:
                continue
                
        return False, "", "Gemini reasoning failed."
