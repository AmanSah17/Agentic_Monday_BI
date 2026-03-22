import logging
from fastapi import APIRouter, HTTPException
from founder_bi_agent.backend.models.schemas import (
    DashboardAllResponse, 
    DateRangeResponse, 
    BusinessMetricsResponse, 
    PipelineDataResponse
)
from founder_bi_agent.backend.service import FounderBIService
from founder_bi_agent.backend.sql.statistical_queries import get_statistical_query
from founder_bi_agent.backend.core.utils import sanitize_for_json

router = APIRouter()
logger = logging.getLogger("founder_bi_analytics")
service = FounderBIService()

@router.get("/dashboard-all", response_model=DashboardAllResponse)
def get_dashboard_all() -> DashboardAllResponse:
    try:
        queries = {
            "dateRange": get_statistical_query("date_horizon"),
            "businessMetrics": get_statistical_query("business_metrics"),
            "dealsPipeline": get_statistical_query("deals_pipeline_stage"),
            "dealsBySector": get_statistical_query("deals_by_sector"),
            "woByStatus": get_statistical_query("work_orders_by_status"),
            "billingFunnel": get_statistical_query("billing_summary"),
            "monthlyDeals": get_statistical_query("monthly_deals"),
            "monthlyRevenue": get_statistical_query("monthly_revenue"),
            "dealStatus": get_statistical_query("deal_status_dist"),
            "invoiceStatus": get_statistical_query("wo_invoice_status"),
            "yieldBySector": get_statistical_query("yield_by_sector"),
            "ownerLeaderboard": get_statistical_query("owner_leaderboard"),
            "clientConcentration": get_statistical_query("client_concentration"),
            "volumeFulfillment": get_statistical_query("volume_fulfillment"),
            "dealSizeDistribution": get_statistical_query("deal_size_distribution"),
            "revenueLeakage": get_statistical_query("revenue_leakage"),
            "executionVelocity": get_statistical_query("execution_velocity"),
            "predictivePipeline": get_statistical_query("predictive_pipeline"),
            "ownerPerformance": get_statistical_query("owner_performance"),
        }
        results = service.execute_dashboard_queries(queries)
        if len(results.get("dateRange", [])) == 1:
            results["dateRange"] = results["dateRange"][0]
        if len(results.get("businessMetrics", [])) == 1:
            results["businessMetrics"] = results["businessMetrics"][0]
        return DashboardAllResponse(data=results)
    except Exception as exc:
        logger.exception("get_dashboard_all.error: %s", str(exc))
        return DashboardAllResponse(data={}, error=str(exc))

@router.get("/date-ranges", response_model=DateRangeResponse)
def get_date_ranges() -> DateRangeResponse:
    try:
        query = get_statistical_query("date_horizon")
        result_df = service.execute_sql_query(query)
        if result_df.empty:
            raise HTTPException(status_code=500, detail="No data returned")
        row = result_df.iloc[0]
        return DateRangeResponse(
            min_date=str(row["min_date"]),
            max_date=str(row["max_date"]),
            distinct_dates=int(row["distinct_dates"]),
            total_days=int(row["total_days"]),
            total_months=int(row.get("total_months", 0)),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/business-metrics", response_model=BusinessMetricsResponse)
def get_business_metrics() -> BusinessMetricsResponse:
    try:
        query = get_statistical_query("business_metrics")
        result_df = service.execute_sql_query(query)
        if result_df.empty:
            raise HTTPException(status_code=500, detail="No data returned")
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
        raise HTTPException(status_code=500, detail=str(exc))

# Generic endpoint for other analytics
@router.get("/{metric_path}", response_model=PipelineDataResponse)
def get_generic_metric(metric_path: str) -> PipelineDataResponse:
    # Map metric_path to query names
    mapping = {
        "deals-pipeline": "deals_pipeline_stage",
        "deals-by-sector": "deals_by_sector",
        "work-orders-by-status": "work_orders_by_status",
        "work-orders-by-sector": "work_orders_by_sector",
        "billing-summary": "billing_summary",
        "monthly-deals": "monthly_deals",
        "monthly-revenue": "monthly_revenue",
        "deal-status": "deal_status_dist",
        "invoice-status": "wo_invoice_status",
        "yield-by-sector": "yield_by_sector",
        "owner-leaderboard": "owner_leaderboard",
        "client-concentration": "client_concentration",
        "volume-fulfillment": "volume_fulfillment",
        "deal-size-distribution": "deal_size_distribution"
    }
    query_name = mapping.get(metric_path)
    if not query_name:
        raise HTTPException(status_code=404, detail="Metric not found")
    try:
        query = get_statistical_query(query_name)
        result_df = service.execute_sql_query(query)
        data = [sanitize_for_json(row.to_dict()) for _, row in result_df.iterrows()]
        return PipelineDataResponse(data=data)
    except Exception as exc:
        return PipelineDataResponse(data=[], error=str(exc))
