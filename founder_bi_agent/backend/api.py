from __future__ import annotations

import uuid
import logging
import time
import math
from datetime import date, datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from founder_bi_agent.backend.history_store import ConversationHistoryStore
from founder_bi_agent.backend.service import FounderBIService

app = FastAPI(title="Founder BI Backend", version="0.1.0")
service = FounderBIService()
history_store = ConversationHistoryStore()
logger = logging.getLogger("founder_bi_api")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    session_id: str | None = None


class QueryResponse(BaseModel):
    session_id: str
    answer: str
    needs_clarification: bool
    clarification_question: str | None = None
    sql_query: str | None = None
    sql_validation_error: str | None = None
    result_records: list[dict[str, Any]] = Field(default_factory=list)
    chart_spec: dict[str, Any] = Field(default_factory=dict)
    quality_report: dict[str, Any] = Field(default_factory=dict)
    board_map: dict[str, Any] = Field(default_factory=dict)
    board_schemas: list[dict[str, Any]] = Field(default_factory=list)
    table_schemas: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    traces: list[dict[str, Any]] = Field(default_factory=list)
    conversation_history_length: int = 0
    history_backend: str = "sqlite"


def _sanitize_for_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if value is pd.NaT:
        return None

    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()

    if isinstance(value, np.generic):
        return _sanitize_for_json(value.item())

    if isinstance(value, dict):
        return {str(k): _sanitize_for_json(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_sanitize_for_json(v) for v in value]

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return str(value)


@app.get("/health")
def health() -> dict[str, Any]:
    status = history_store.status()
    return {
        "status": "ok",
        "history_backend": getattr(status, "backend", "sqlite"),
    }


@app.get("/history/{session_id}")
def get_history(session_id: str) -> dict[str, Any]:
    history = history_store.get_history(session_id)
    status = history_store.status()
    return {
        "session_id": session_id,
        "history": history,
        "history_length": len(history),
        "history_backend": status.backend,
    }


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    started = time.perf_counter()
    session_id = payload.session_id or str(uuid.uuid4())
    cached_history = history_store.get_history(session_id)

    incoming = [
        {"role": str(t.get("role", "")), "content": str(t.get("content", ""))}
        for t in payload.conversation_history
    ]
    merged_history = cached_history if cached_history else incoming

    logger.info(
        "query.start session_id=%s question_len=%s cached_history=%s incoming_history=%s",
        session_id,
        len(payload.question),
        len(cached_history),
        len(incoming),
    )
    try:
        result = service.run_query(
            question=payload.question,
            conversation_history=merged_history,
        )
    except Exception as exc:
        logger.exception("query.error session_id=%s error=%s", session_id, str(exc))
        import traceback
        history_store.log_error(session_id, exc.__class__.__name__, str(exc), traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"backend_query_error: {exc.__class__.__name__}: {str(exc)}",
        ) from exc

    safe_result = _sanitize_for_json(result)

    if safe_result.get("sql_validation_error"):
        history_store.log_error(session_id, "sql_validation_error", str(safe_result["sql_validation_error"]))
    if safe_result.get("sql_execution_error"):
        history_store.log_error(session_id, "sql_execution_error", str(safe_result["sql_execution_error"]))
    ans = safe_result.get("answer") or ""
    if "error generating the final insight" in str(ans).lower() or "error code: 401" in str(ans).lower():
        history_store.log_error(session_id, "insight_generation_error", str(ans))
        logger.error(f"🔴 EVENT ALARM: Critical LLM Pipeline Failure: {ans}")

    assistant_text = safe_result.get("answer") or safe_result.get("clarification_question") or ""
    updated_history = history_store.append_turns(
        session_id,
        [
            {"role": "user", "content": payload.question},
            {"role": "assistant", "content": assistant_text},
        ],
    )
    status = history_store.status()

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "query.done session_id=%s elapsed_ms=%s rows=%s traces=%s history_len=%s",
        session_id,
        elapsed_ms,
        len(safe_result.get("result_records", [])),
        len(safe_result.get("traces", [])),
        len(updated_history),
    )
    return QueryResponse(
        session_id=session_id,
        conversation_history_length=len(updated_history),
        history_backend=status.backend,
        **safe_result,
    )
