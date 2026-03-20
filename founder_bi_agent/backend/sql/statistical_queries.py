"""
Pre-built statistical queries for robust fallback and analytics.
These are deterministic, tested queries that don't depend on LLM generation.
Used by: analytics endpoints, fallback strategy, dashboard initialization.
"""

from typing import Literal


def get_date_horizon_query() -> str:
    """
    Query to determine the total date range across both tables.
    Answers: "What is the total time horizon in both tables?"
    
    Returns:
        min_date: Earliest date across all tables
        max_date: Latest date across all tables
        distinct_dates: Count of unique dates
        total_days: Total span in days
    """
    return """
    SELECT
      CAST(MIN(event_date) AS VARCHAR) AS min_date,
      CAST(MAX(event_date) AS VARCHAR) AS max_date,
      COUNT(DISTINCT event_date) AS distinct_dates,
      DATEDIFF('day', MIN(event_date), MAX(event_date)) AS total_days,
      DATEDIFF('month', MIN(event_date), MAX(event_date)) AS total_months
    FROM (
      SELECT TRY_CAST(created_date AS DATE) AS event_date FROM deals WHERE created_date IS NOT NULL
      UNION ALL
      SELECT TRY_CAST(tentative_close_date AS DATE) AS event_date FROM deals WHERE tentative_close_date IS NOT NULL
      UNION ALL
      SELECT TRY_CAST(created_at AS DATE) AS event_date FROM work_orders WHERE created_at IS NOT NULL
      UNION ALL
      SELECT TRY_CAST(probable_start_date AS DATE) AS event_date FROM work_orders WHERE probable_start_date IS NOT NULL
      UNION ALL
      SELECT TRY_CAST(probable_end_date AS DATE) AS event_date FROM work_orders WHERE probable_end_date IS NOT NULL
    ) AS all_dates
    WHERE event_date IS NOT NULL
    """


def get_business_metrics_query() -> str:
    """
    High-level KPIs: total pipeline value, deal counts, collection metrics.
    
    Returns:
        Deals: count, total pipeline value, sector count, stage count
        Work Orders: count, total value, billed, collected, collection rate
    """
    return """
    WITH deals_metrics AS (
      SELECT
        COUNT(*) AS total_deals,
        SUM(COALESCE(masked_deal_value, 0)) AS total_pipeline_value,
        COUNT(DISTINCT sectorservice) AS sector_count,
        COUNT(DISTINCT deal_stage) AS stage_count
      FROM deals
    ),
    work_orders_metrics AS (
      SELECT
        COUNT(*) AS total_wo,
        SUM(COALESCE(amount_in_rupees_incl_of_gst_masked, 0)) AS total_wo_value,
        SUM(COALESCE(billed_value_in_rupees_incl_of_gst_masked, 0)) AS total_billed,
        SUM(COALESCE(collected_amount_in_rupees_incl_of_gst_masked, 0)) AS total_collected,
        CASE 
          WHEN SUM(COALESCE(amount_in_rupees_incl_of_gst_masked, 0)) > 0
          THEN ROUND(100.0 * SUM(COALESCE(collected_amount_in_rupees_incl_of_gst_masked, 0)) / SUM(COALESCE(amount_in_rupees_incl_of_gst_masked, 0)), 2)
          ELSE 0
        END AS collection_rate_pct
      FROM work_orders
    )
    SELECT
      d.total_deals,
      d.total_pipeline_value,
      d.sector_count,
      w.total_wo,
      w.total_wo_value,
      w.total_billed,
      w.total_collected,
      w.collection_rate_pct
    FROM deals_metrics d, work_orders_metrics w
    """


def get_deals_pipeline_by_stage() -> str:
    """
    Deals segmented by stage, showing count and total value per stage.
    """
    return """
    SELECT
      COALESCE(deal_stage, 'Unknown') AS stage,
      COUNT(*) AS deal_count,
      SUM(COALESCE(masked_deal_value, 0)) AS total_value,
      ROUND(AVG(COALESCE(masked_deal_value, 0)), 2) AS avg_deal_value,
      ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
    FROM deals
    GROUP BY 1
    ORDER BY total_value DESC
    """


def get_deals_by_sector() -> str:
    """
    Revenue pipeline by sector/service.
    """
    return """
    SELECT
      COALESCE(sectorservice, 'Unknown') AS sector,
      COUNT(*) AS deal_count,
      SUM(COALESCE(masked_deal_value, 0)) AS total_value,
      ROUND(AVG(COALESCE(masked_deal_value, 0)), 2) AS avg_deal_value,
      ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
    FROM deals
    GROUP BY 1
    ORDER BY total_value DESC
    """


def get_work_orders_by_status() -> str:
    """
    Work orders segmented by execution status.
    """
    return """
    SELECT
      COALESCE(execution_status, 'Unknown') AS status,
      COUNT(*) AS wo_count,
      SUM(COALESCE(amount_in_rupees_incl_of_gst_masked, 0)) AS total_value,
      SUM(COALESCE(billed_value_in_rupees_incl_of_gst_masked, 0)) AS total_billed,
      SUM(COALESCE(collected_amount_in_rupees_incl_of_gst_masked, 0)) AS total_collected,
      ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
    FROM work_orders
    GROUP BY 1
    ORDER BY total_value DESC
    """


def get_work_orders_by_sector() -> str:
    """
    Work orders segmented by sector.
    """
    return """
    SELECT
      COALESCE(sector, 'Unknown') AS sector,
      COUNT(*) AS wo_count,
      SUM(COALESCE(amount_in_rupees_incl_of_gst_masked, 0)) AS total_value,
      SUM(COALESCE(billed_value_in_rupees_incl_of_gst_masked, 0)) AS total_billed,
      SUM(COALESCE(collected_amount_in_rupees_incl_of_gst_masked, 0)) AS total_collected
    FROM work_orders
    GROUP BY 1
    ORDER BY total_value DESC
    """


def get_billing_collection_summary() -> str:
    """
    Work order billing and collection funnel.
    """
    return """
    SELECT
      COUNT(*) AS total_wo,
      SUM(COALESCE(amount_in_rupees_incl_of_gst_masked, 0)) AS total_wo_value,
      SUM(COALESCE(billed_value_in_rupees_incl_of_gst_masked, 0)) AS total_billed_value,
      SUM(COALESCE(collected_amount_in_rupees_incl_of_gst_masked, 0)) AS total_collected_value,
      SUM(COALESCE(amount_receivable_masked, 0)) AS total_receivable,
      ROUND(100.0 * SUM(COALESCE(billed_value_in_rupees_incl_of_gst_masked, 0)) / 
            NULLIF(SUM(COALESCE(amount_in_rupees_incl_of_gst_masked, 0)), 0), 2) AS billing_completion_pct,
      ROUND(100.0 * SUM(COALESCE(collected_amount_in_rupees_incl_of_gst_masked, 0)) / 
            NULLIF(SUM(COALESCE(billed_value_in_rupees_incl_of_gst_masked, 0)), 0), 2) AS collection_rate_pct
    FROM work_orders
    """


def get_monthly_deals_trend() -> str:
    """
    Time-series: deal creation and expected closure by month.
    """
    return """
    SELECT
      DATE_TRUNC('month', TRY_CAST(created_date AS DATE)) AS month,
      COUNT(*) AS deals_created,
      SUM(COALESCE(masked_deal_value, 0)) AS value_created
    FROM deals
    WHERE created_date IS NOT NULL
    GROUP BY 1
    ORDER BY 1 ASC
    """


def get_monthly_revenue_trend() -> str:
    """
    Time-series: work order project value and billing/collection by month.
    """
    return """
    SELECT
      DATE_TRUNC('month', TRY_CAST(probable_start_date AS DATE)) AS month,
      COUNT(*) AS wo_started,
      SUM(COALESCE(amount_in_rupees_incl_of_gst_masked, 0)) AS project_value,
      SUM(COALESCE(billed_value_in_rupees_incl_of_gst_masked, 0)) AS billed_value,
      SUM(COALESCE(collected_amount_in_rupees_incl_of_gst_masked, 0)) AS collected_value
    FROM work_orders
    WHERE probable_start_date IS NOT NULL
    GROUP BY 1
    ORDER BY 1 ASC
    """


def get_deal_status_distribution() -> str:
    """
    Pie chart data: deals by status (Open, On Hold, Won, Lost).
    """
    return """
    SELECT
      COALESCE(deal_status, 'Unknown') AS status,
      COUNT(*) AS deal_count,
      SUM(COALESCE(masked_deal_value, 0)) AS total_value
    FROM deals
    GROUP BY 1
    ORDER BY deal_count DESC
    """


def get_work_order_invoice_status() -> str:
    """
    Waterfall: invoice status breakdown.
    """
    return """
    SELECT
      COALESCE(invoice_status, 'Unknown') AS billing_status,
      COUNT(*) AS wo_count,
      SUM(COALESCE(amount_in_rupees_incl_of_gst_masked, 0)) AS wo_value,
      SUM(COALESCE(billed_value_in_rupees_incl_of_gst_masked, 0)) AS billed_value
    FROM work_orders
    GROUP BY 1
    ORDER BY wo_value DESC
    """


def get_statistical_query(query_type: Literal[
    "date_horizon",
    "business_metrics",
    "deals_pipeline_stage",
    "deals_by_sector",
    "work_orders_by_status",
    "work_orders_by_sector",
    "billing_summary",
    "monthly_deals",
    "monthly_revenue",
    "deal_status_dist",
    "wo_invoice_status",
]) -> str:
    """
    Fetch a pre-built statistical query by type.
    
    Args:
        query_type: One of the predefined query types
        
    Returns:
        Valid DuckDB SQL query string
        
    Raises:
        ValueError: If query_type is not recognized
    """
    queries = {
        "date_horizon": get_date_horizon_query,
        "business_metrics": get_business_metrics_query,
        "deals_pipeline_stage": get_deals_pipeline_by_stage,
        "deals_by_sector": get_deals_by_sector,
        "work_orders_by_status": get_work_orders_by_status,
        "work_orders_by_sector": get_work_orders_by_sector,
        "billing_summary": get_billing_collection_summary,
        "monthly_deals": get_monthly_deals_trend,
        "monthly_revenue": get_monthly_revenue_trend,
        "deal_status_dist": get_deal_status_distribution,
        "wo_invoice_status": get_work_order_invoice_status,
    }
    
    if query_type not in queries:
        raise ValueError(f"Unknown query type: {query_type}. Valid types: {list(queries.keys())}")
    
    return queries[query_type]()
