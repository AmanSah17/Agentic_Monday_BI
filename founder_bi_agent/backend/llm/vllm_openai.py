from __future__ import annotations

from typing import Any

from founder_bi_agent.backend.config import AgentSettings


class VLLMSQLPlanner:
    """
    SQL planner using an OpenAI-compatible endpoint (vLLM server).
    """

    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self._clients: dict[str, Any] = {}
        self.last_generation_meta: dict[str, Any] = {
            "provider": settings.llm_provider,
            "mode": "uninitialized",
        }

    def _create_client(self, model: str) -> Any:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Install langchain-openai to use vLLM OpenAI-compatible planner."
            ) from exc

        base_url = self.settings.llm_base_url.strip().rstrip("/")
        api_key = self.settings.llm_api_key or "EMPTY"
        target_model = model

        if self.settings.llm_provider == "huggingface":
            base_url = "https://router.huggingface.co/v1"
            api_key = self.settings.huggingface_api_key
            target_model = "deepseek-ai/DeepSeek-R1" # Excellent for SQL

        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"

        return ChatOpenAI(
            model=target_model,
            api_key=api_key,
            base_url=base_url,
            temperature=0,
            timeout=120,
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

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        raw = text.strip()
        if raw.startswith("```") and raw.endswith("```"):
            lines = raw.splitlines()
            if len(lines) >= 3:
                raw = "\n".join(lines[1:-1]).strip()
        return raw

    def generate_sql(self, question: str, schema_hint: str, fallback_sql: str) -> str:
        if self.settings.llm_provider not in {"vllm", "openai_compat", "openai", "huggingface"}:
            self.last_generation_meta = {
                "provider": self.settings.llm_provider,
                "mode": "fallback_non_vllm_provider",
            }
            return fallback_sql

        candidates = self._candidate_models()
        failures: list[dict[str, str]] = []

        prompt = (
            "You are a strict analytics SQL assistant for DuckDB.\n"
            "Return exactly one read-only SQL query.\n"
            "Use only existing tables/columns in schema.\n"
            "No markdown.\n\n"
            f"Schema:\n{schema_hint}\n\n"
            f"Question:\n{question}\n"
        )

        for model in candidates:
            try:
                client = self._get_client(model)
                response = client.invoke(prompt)
                sql_text = getattr(response, "content", "") or ""
                sql_text = self._strip_code_fences(str(sql_text))
                if not sql_text.strip():
                    failures.append({"model": model, "error": "empty_sql_output"})
                    continue
                self.last_generation_meta = {
                    "provider": "vllm",
                    "mode": "llm_sql_generated",
                    "model": model,
                    "attempted_models": candidates,
                    "failures_before_success": failures,
                    "base_url": self.settings.llm_base_url,
                }
                return sql_text
            except Exception as exc:
                failures.append({"model": model, "error": str(exc)})

        self.last_generation_meta = {
            "provider": "vllm",
            "mode": "fallback_all_models_failed",
            "attempted_models": candidates,
            "errors": failures,
            "base_url": self.settings.llm_base_url,
        }
        return fallback_sql

