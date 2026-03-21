from __future__ import annotations

import json
from typing import Any

from founder_bi_agent.backend.config import AgentSettings


class GLMFoundationClient:
    """
    Foundation reasoning client using GLM-4.5-Air (ZhipuAI) via OpenAI-compatible API.
    Handles semantic routing, clarification, and insight writing.
    """

    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self._client = self._create_client()

    def _create_client(self) -> Any:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Install langchain-openai to use ZhipuAI / GLM foundation client."
            ) from exc

        model_name = getattr(self.settings, "llm_reasoning_model", "glm-4.5-air") or "glm-4.5-air"
        api_key = self.settings.zhipuai_api_key or "EMPTY"
        base_url = self.settings.zhipuai_base_url
        
        if "siliconflow" in str(self.settings.zhipuai_base_url).lower():
            model_name = "THUDM/glm-4-9b-chat"
            
        if self.settings.llm_provider == "huggingface":
            model_name = "deepseek-ai/DeepSeek-R1"
            api_key = self.settings.huggingface_api_key
            base_url = "https://router.huggingface.co/v1/"

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.1,
            max_retries=2,
            timeout=120,
        )

    def route_intent(self, question: str) -> str:
        prompt = (
            "You are an intent router for a Monday.com BI Agent.\n"
            "Classify the user's question into exactly one of these intents:\n"
            "- 'pipeline_health': queries related to deal funnel, pipeline value, deal stages, or sales.\n"
            "- 'general_bi': queries related to work orders, billing, receivables, collections, or general operations.\n\n"
            f"Question: {question}\n\n"
            "Respond ONLY with the intent string (e.g., 'pipeline_health' or 'general_bi') and nothing else."
        )
        try:
            response = self._client.invoke(prompt)
            intent = str(getattr(response, "content", "")).strip().lower()
            if intent in {"pipeline_health", "general_bi"}:
                return intent
        except Exception:
            pass
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
        try:
            response = self._client.invoke(prompt)
            content = str(getattr(response, "content", "")).strip()
            
            # Remove Markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            data = json.loads(content.strip())
            return bool(data.get("needs_clarification")), str(data.get("clarification_question", ""))
        except Exception:
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
            data_preview = result_df.head(500).to_markdown()
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
        
        try:
            response = self._client.invoke(prompt)
            return str(getattr(response, "content", "")).strip()
        except Exception as e:
            fallback = "I ran a live analysis but encountered an error generating the final insight summary: " + str(e)
            return fallback

