from __future__ import annotations

import json

from founder_bi_agent.backend.config import AgentSettings
from founder_bi_agent.backend.llm.google_gemini import GeminiSQLPlanner


def main() -> None:
    settings = AgentSettings.from_env()
    planner = GeminiSQLPlanner(settings)
    models = [settings.llm_sql_model, *settings.llm_sql_model_variants]
    # unique preserving order
    seen = set()
    candidates = []
    for m in models:
        if m and m not in seen:
            seen.add(m)
            candidates.append(m)

    results = []
    for model in candidates:
        planner.settings.llm_sql_model = model
        planner.settings.llm_sql_model_variants = []
        _ = planner.generate_sql(
            question="Count deals by stage.",
            schema_hint="- deals(deal_stage:object)",
            fallback_sql="SELECT 1",
        )
        meta = dict(planner.last_generation_meta)
        status = "ok" if meta.get("mode") == "llm_sql_generated" else "failed"
        results.append({"model": model, "status": status, "meta": meta})
        print(json.dumps(results[-1], ensure_ascii=True, indent=2))

    print("\nSummary:")
    ok = [r["model"] for r in results if r["status"] == "ok"]
    failed = [r["model"] for r in results if r["status"] != "ok"]
    print(f"working_models={ok}")
    print(f"failed_models={failed}")


if __name__ == "__main__":
    main()
