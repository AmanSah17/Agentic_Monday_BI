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

import os

allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000")
allowed_origins = [o.strip() for o in allowed_origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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


# ============================================================================
# PHASE 3: ANALYTICS ENDPOINTS
# ============================================================================

class DateRangeResponse(BaseModel):
    min_date: str
    max_date: str
    distinct_dates: int
    total_days: int
    total_months: int


class BusinessMetricsResponse(BaseModel):
    total_deals: int
    total_pipeline_value: float
    sector_count: int
    total_wo: int
    total_wo_value: float
    total_billed: float
    total_collected: float
    collection_rate_pct: float


class PipelineDataResponse(BaseModel):
    data: list[dict[str, Any]]
    error: str | None = None


@app.get("/analytics/date-ranges", response_model=DateRangeResponse)
def get_date_ranges() -> DateRangeResponse:
    """
    Get total date horizon across both tables (Deals and Work Orders).
    
    Returns:
        - min_date: Earliest date across all date columns
        - max_date: Latest date across all date columns
        - distinct_dates: Count of unique dates
        - total_days: Total span in days
        - total_months: Total span in months
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("date_horizon")
        result_df = svc.execute_sql_query(query)
        
        if result_df.empty:
            raise HTTPException(status_code=500, detail="No data returned from date_horizon query")
        
        row = result_df.iloc[0]
        return DateRangeResponse(
            min_date=str(row["min_date"]),
            max_date=str(row["max_date"]),
            distinct_dates=int(row["distinct_dates"]),
            total_days=int(row["total_days"]),
            total_months=int(row.get("total_months", 0)),
        )
    except Exception as exc:
        logger.exception("get_date_ranges.error: %s", str(exc))
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(exc)}") from exc


@app.get("/analytics/business-metrics", response_model=BusinessMetricsResponse)
def get_business_metrics() -> BusinessMetricsResponse:
    """
    Get high-level KPIs: pipeline, work order, billing and collection metrics.
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("business_metrics")
        result_df = svc.execute_sql_query(query)
        
        if result_df.empty:
            raise HTTPException(status_code=500, detail="No data returned from business_metrics query")
        
        row = result_df.iloc[0]
        return BusinessMetricsResponse(
            total_deals=int(row["total_deals"]),
            total_pipeline_value=float(row["total_pipeline_value"]),
            sector_count=int(row["sector_count"]),
            total_wo=int(row["total_wo"]),
            total_wo_value=float(row["total_wo_value"]),
            total_billed=float(row["total_billed"]),
            total_collected=float(row["total_collected"]),
            collection_rate_pct=float(row["collection_rate_pct"]),
        )
    except Exception as exc:
        logger.exception("get_business_metrics.error: %s", str(exc))
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(exc)}") from exc


@app.get("/analytics/deals-pipeline", response_model=PipelineDataResponse)
def get_deals_pipeline() -> PipelineDataResponse:
    """
    Get deals segmented by pipeline stage.
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("deals_pipeline_stage")
        result_df = svc.execute_sql_query(query)
        
        data = [_sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        logger.exception("get_deals_pipeline.error: %s", str(exc))
        return PipelineDataResponse(data=[], error=str(exc))


@app.get("/analytics/deals-by-sector", response_model=PipelineDataResponse)
def get_deals_by_sector() -> PipelineDataResponse:
    """
    Get deals segmented by sector/service.
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("deals_by_sector")
        result_df = svc.execute_sql_query(query)
        
        data = [_sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        logger.exception("get_deals_by_sector.error: %s", str(exc))
        return PipelineDataResponse(data=[], error=str(exc))


@app.get("/analytics/work-orders-by-status", response_model=PipelineDataResponse)
def get_work_orders_by_status() -> PipelineDataResponse:
    """
    Get work orders segmented by execution status.
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("work_orders_by_status")
        result_df = svc.execute_sql_query(query)
        
        data = [_sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        logger.exception("get_work_orders_by_status.error: %s", str(exc))
        return PipelineDataResponse(data=[], error=str(exc))


@app.get("/analytics/work-orders-by-sector", response_model=PipelineDataResponse)
def get_work_orders_by_sector_endpoint() -> PipelineDataResponse:
    """
    Get work orders segmented by sector.
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("work_orders_by_sector")
        result_df = svc.execute_sql_query(query)
        
        data = [_sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        logger.exception("get_work_orders_by_sector.error: %s", str(exc))
        return PipelineDataResponse(data=[], error=str(exc))


@app.get("/analytics/billing-summary", response_model=PipelineDataResponse)
def get_billing_summary() -> PipelineDataResponse:
    """
    Get work order billing and collection funnel.
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("billing_summary")
        result_df = svc.execute_sql_query(query)
        
        data = [_sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        logger.exception("get_billing_summary.error: %s", str(exc))
        return PipelineDataResponse(data=[], error=str(exc))


@app.get("/analytics/monthly-deals", response_model=PipelineDataResponse)
def get_monthly_deals() -> PipelineDataResponse:
    """
    Get time-series: deal creation and expected closure by month.
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("monthly_deals")
        result_df = svc.execute_sql_query(query)
        
        data = [_sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        logger.exception("get_monthly_deals.error: %s", str(exc))
        return PipelineDataResponse(data=[], error=str(exc))


@app.get("/analytics/monthly-revenue", response_model=PipelineDataResponse)
def get_monthly_revenue() -> PipelineDataResponse:
    """
    Get time-series: work order project value and billing/collection by month.
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("monthly_revenue")
        result_df = svc.execute_sql_query(query)
        
        data = [_sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        logger.exception("get_monthly_revenue.error: %s", str(exc))
        return PipelineDataResponse(data=[], error=str(exc))


@app.get("/analytics/deal-status", response_model=PipelineDataResponse)
def get_deal_status() -> PipelineDataResponse:
    """
    Get deal distribution by status (Open, On Hold, Won, Lost).
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("deal_status_dist")
        result_df = svc.execute_sql_query(query)
        
        data = [_sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        logger.exception("get_deal_status.error: %s", str(exc))
        return PipelineDataResponse(data=[], error=str(exc))


@app.get("/analytics/invoice-status", response_model=PipelineDataResponse)
def get_invoice_status() -> PipelineDataResponse:
    """
    Get work order invoice/billing status breakdown.
    """
    try:
        from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
        from founder_bi_agent.backend.service import FounderBIService
        
        svc = FounderBIService()
        query = get_statistical_query("wo_invoice_status")
        result_df = svc.execute_sql_query(query)
        
        data = [_sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        logger.exception("get_invoice_status.error: %s", str(exc))
        return PipelineDataResponse(data=[], error=str(exc))

# ============================================================================
# PHASE 4: UNIFIED SINGLE PAGE APPLICATION (SPA) SERVING
# ============================================================================
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

dist_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Natively intercept React Router domain fallbacks
        return FileResponse(os.path.join(dist_dir, "index.html"))
