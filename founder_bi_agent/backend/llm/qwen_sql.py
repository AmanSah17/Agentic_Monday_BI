from __future__ import annotations

from typing import Any

from founder_bi_agent.backend.core.config import AgentSettings


class QwenSQLPlanner:
    """
    SQL planner implementing specialized prompting for Qwen Text-to-SQL model.
    """

    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self._clients: dict[str, Any] = {}
        self.last_generation_meta: dict[str, Any] = {
            "provider": getattr(settings, "llm_provider", "qwen"),
            "mode": "uninitialized",
        }

    def _create_client(self, model: str) -> Any:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Install langchain-openai to use Qwen SQL planner."
            ) from exc

        return ChatOpenAI(
            model=model,
            api_key=getattr(self.settings, "qwen_api_key", "EMPTY") or "EMPTY",
            base_url=getattr(self.settings, "qwen_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            temperature=0,
            max_retries=1,
            timeout=30,
        )

    def _get_client(self, model: str) -> Any:
        if model not in self._clients:
            self._clients[model] = self._create_client(model)
        return self._clients[model]

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        raw = text.strip()
        if raw.startswith("```sql"):
            raw = raw[6:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        return raw.strip()

    def generate_sql(self, question: str, schema_hint: str, fallback_sql: str) -> str:
        failures: list[dict[str, str]] = []
        
        # Use qwen-coder or qwen-turbo based on the user's config
        model = getattr(self.settings, "llm_sql_model", "qwen-coder-plus") or "qwen-coder-plus"
        if "siliconflow" in str(getattr(self.settings, "qwen_base_url", "")).lower():
            model = "Qwen/Qwen2.5-Coder-32B-Instruct"

        prompt = (
            "You are an expert DuckDB SQL data analyst. You write advanced analytical queries based on provided schemas.\n\n"
            f"Schema:\n{schema_hint}\n\n"
            f"Question: {question}\n\n"
            "Instructions:\n"
            "1. Output exactly one valid, executable DuckDB SQL query.\n"
            "2. Read only data (SELECT). Never mutate.\n"
            "3. Do not include markdown formatting or explanations, just the SQL string.\n"
            "4. Handle edge cases like NULL values where appropriate with COALESCE.\n"
            "5. The output should be directly executable."
        )

        try:
            client = self._get_client(model)
            response = client.invoke(prompt)
            sql_text = getattr(response, "content", "") or ""
            sql_text = self._strip_code_fences(str(sql_text))
            
            if not sql_text.strip():
                self.last_generation_meta = {
                    "provider": "qwen",
                    "mode": "fallback_empty_output",
                    "attempted_model": model,
                }
                return fallback_sql
                
            self.last_generation_meta = {
                "provider": "qwen",
                "mode": "llm_sql_generated",
                "model": model,
                "base_url": getattr(self.settings, "qwen_base_url", ""),
            }
            return sql_text
        except Exception as exc:
            self.last_generation_meta = {
                "provider": "qwen",
                "mode": "fallback_exception",
                "error": str(exc),
                "attempted_model": model,
            }
            return fallback_sql

