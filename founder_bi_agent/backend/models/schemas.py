from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    session_id: Optional[str] = None

class TraceEntry(BaseModel):
    ts: Optional[str] = None
    node: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class QueryResponse(BaseModel):
    session_id: str
    answer: str
    needs_clarification: bool
    clarification_question: Optional[str] = None
    sql_query: Optional[str] = None
    sql_validation_error: Optional[str] = None
    result_records: List[Dict[str, Any]] = Field(default_factory=list)
    chart_spec: Dict[str, Any] = Field(default_factory=dict)
    quality_report: Dict[str, Any] = Field(default_factory=dict)
    board_map: Dict[str, Any] = Field(default_factory=dict)
    board_schemas: List[Dict[str, Any]] = Field(default_factory=list)
    table_schemas: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    traces: List[Dict[str, Any]] = Field(default_factory=list)
    last_result_summary: Optional[str] = None
    conversation_history_length: int = 0
    history_backend: str = "sqlite"

class DashboardAllResponse(BaseModel):
    data: Dict[str, Any]
    error: Optional[str] = None

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
    data: List[Dict[str, Any]]
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    history_backend: str
