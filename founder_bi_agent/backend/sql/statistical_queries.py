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
        SUM(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)) AS total_pipeline_value,
        COUNT(DISTINCT sectorservice) AS sector_count,
        COUNT(DISTINCT deal_stage) AS stage_count
      FROM deals
    ),
    work_orders_metrics AS (
      SELECT
        COUNT(*) AS total_wo,
        SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_wo_value,
        SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_billed,
        SUM(COALESCE(TRY_CAST(collected_amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_collected,
        CASE 
          WHEN SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) > 0
          THEN ROUND(100.0 * SUM(COALESCE(TRY_CAST(collected_amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) / SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)), 2)
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
      SUM(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)) AS total_value,
      ROUND(AVG(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)), 2) AS avg_deal_value,
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
      SUM(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)) AS total_value,
      ROUND(AVG(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)), 2) AS avg_deal_value,
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
      SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_value,
      SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_billed,
      SUM(COALESCE(TRY_CAST(collected_amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_collected,
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
      SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_value,
      SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_billed,
      SUM(COALESCE(TRY_CAST(collected_amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_collected
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
      SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_wo_value,
      SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_billed_value,
      SUM(COALESCE(TRY_CAST(collected_amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_collected_value,
      SUM(COALESCE(TRY_CAST(amount_receivable_masked AS DOUBLE), 0)) AS total_receivable,
      ROUND(100.0 * SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) / 
            NULLIF(SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)), 0), 2) AS billing_completion_pct,
      ROUND(100.0 * SUM(COALESCE(TRY_CAST(collected_amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) / 
            NULLIF(SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)), 0), 2) AS collection_rate_pct
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
      SUM(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)) AS value_created
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
      SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS project_value,
      SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS billed_value,
      SUM(COALESCE(TRY_CAST(collected_amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS collected_value
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
      SUM(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)) AS total_value
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
      SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS wo_value,
      SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS billed_value
    FROM work_orders
    GROUP BY 1
    ORDER BY wo_value DESC
    """


def get_yield_by_sector() -> str:
    """
    Cross-table Yield Conversion by Sector.
    Compares Total Deals Pipeline vs Actual Won & Billed.
    """
    return """
    SELECT
      COALESCE(d.sectorservice, 'Unknown') AS sector,
      COUNT(DISTINCT d.item_id) AS total_deals,
      SUM(COALESCE(TRY_CAST(d.masked_deal_value AS DOUBLE), 0)) AS pipeline_value,
      COUNT(DISTINCT w.item_id) AS won_work_orders,
      SUM(COALESCE(TRY_CAST(w.amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS actual_realized_value,
      CASE 
        WHEN SUM(COALESCE(TRY_CAST(d.masked_deal_value AS DOUBLE), 0)) > 0 
        THEN ROUND(100.0 * SUM(COALESCE(TRY_CAST(w.amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) / SUM(COALESCE(TRY_CAST(d.masked_deal_value AS DOUBLE), 0)), 2)
        ELSE 0 
      END AS yield_pct
    FROM deals d
    LEFT JOIN work_orders w ON d.item_name = w.item_name
    GROUP BY 1
    ORDER BY pipeline_value DESC
    """

def get_owner_leaderboard() -> str:
    """
    Sales Rep (Owner) Leaderboard.
    """
    return """
    SELECT
      COALESCE(d.owner_code, 'Unassigned') AS owner_name,
      COUNT(d.item_id) AS deals_generated,
      SUM(COALESCE(TRY_CAST(d.masked_deal_value AS DOUBLE), 0)) AS pipeline_generated,
      SUM(CASE WHEN d.deal_status = 'Won' THEN 1 ELSE 0 END) AS deals_won,
      SUM(CASE WHEN d.deal_status = 'Won' THEN COALESCE(TRY_CAST(d.masked_deal_value AS DOUBLE), 0) ELSE 0 END) AS value_won
    FROM deals d
    GROUP BY 1
    ORDER BY pipeline_generated DESC
    LIMIT 15
    """

def get_client_concentration() -> str:
    """
    Pareto analysis: Top 10 Clients by pipeline and billed value.
    """
    return """
    SELECT
      COALESCE(d.client_code, 'Unknown') AS client_name,
      COUNT(DISTINCT d.item_id) AS total_deals,
      SUM(COALESCE(TRY_CAST(d.masked_deal_value AS DOUBLE), 0)) AS total_pipeline_value,
      SUM(COALESCE(TRY_CAST(w.billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS total_billed_value
    FROM deals d
    LEFT JOIN work_orders w ON d.item_name = w.item_name
    GROUP BY 1
    ORDER BY total_pipeline_value DESC
    LIMIT 10
    """

def get_volume_fulfillment() -> str:
    """
    Operational Volume vs Fulfillment by Sector.
    """
    return """
    SELECT
      COALESCE(sector, 'Unknown') AS sector,
      SUM(TRY_CAST(COALESCE(quantity_by_ops, '0') AS DOUBLE)) AS ops_quantity,
      SUM(TRY_CAST(COALESCE(quantity_billed_till_date, '0') AS DOUBLE)) AS billed_quantity,
      SUM(TRY_CAST(COALESCE(balance_in_quantity, '0') AS DOUBLE)) AS balance_quantity
    FROM work_orders
    GROUP BY 1
    ORDER BY ops_quantity DESC
    """

def get_deal_size_distribution() -> str:
    """
    Average Deal Size Distribution segmented by Nature of Work (if joined) or deal stage.
    We proxy 'Nature of Work' using product_deal from deals table since it's the forecast side.
    """
    return """
    SELECT
      COALESCE(product_deal, 'Misc') AS product_type,
      COUNT(*) AS deal_count,
      ROUND(AVG(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)), 2) AS avg_deal_size,
      SUM(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)) AS total_volume
    FROM deals
    WHERE TRY_CAST(masked_deal_value AS DOUBLE) > 0
    GROUP BY 1
    ORDER BY total_volume DESC
    LIMIT 10
    """

def get_revenue_leakage() -> str:
    """
    Revenue Leakage Waterfall (Sector vs collection drop-off).
    """
    return """
    SELECT
      COALESCE(sector, 'Unknown') AS sector,
      SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS quoted_value,
      SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS billed_value,
      SUM(COALESCE(TRY_CAST(collected_amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS collected_value,
      SUM(COALESCE(TRY_CAST(amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) - SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS unbilled_leakage,
      SUM(COALESCE(TRY_CAST(billed_value_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) - SUM(COALESCE(TRY_CAST(collected_amount_in_rupees_incl_of_gst_masked AS DOUBLE), 0)) AS uncollected_leakage
    FROM work_orders
    GROUP BY 1
    ORDER BY quoted_value DESC
    LIMIT 10
    """

def get_execution_velocity() -> str:
    """
    Execution Velocity Analysis (Probable vs Actual Dates).
    """
    return """
    WITH wo_stats AS (
      SELECT
        COALESCE(execution_status, 'Unknown') AS status,
        'Work Order' as type,
        COUNT(*) AS volume,
        AVG(CASE 
          WHEN TRY_CAST(probable_start_date AS DATE) IS NOT NULL 
           AND TRY_CAST(actual_billing_month AS DATE) IS NOT NULL
          THEN DATEDIFF('day', TRY_CAST(probable_start_date AS DATE), TRY_CAST(actual_billing_month AS DATE))
          ELSE NULL 
        END) AS avg_days_to_bill
      FROM work_orders
      GROUP BY 1, 2
    ),
    deal_stats AS (
      SELECT
        COALESCE(deal_stage, 'Unknown') AS status,
        'Deal' as type,
        COUNT(*) AS volume,
        NULL::DOUBLE AS avg_days_to_bill
      FROM deals
      GROUP BY 1, 2
    )
    SELECT 
      status as execution_status,
      type,
      volume as project_count,
      ROUND(COALESCE(avg_days_to_bill, 0), 1) as avg_days_to_bill
    FROM (SELECT * FROM wo_stats UNION ALL SELECT * FROM deal_stats)
    ORDER BY volume DESC
    """

def get_predictive_pipeline() -> str:
    """
    Predictive Pipeline Matrix (Status vs Probability).
    """
    return """
    SELECT
      COALESCE(deal_status, 'Unknown') AS deal_status,
      COALESCE(closure_probability, 'Unknown') AS closure_probability,
      COUNT(*) AS deal_count,
      SUM(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)) AS pipeline_revenue
    FROM deals
    WHERE TRY_CAST(masked_deal_value AS DOUBLE) > 0
    GROUP BY 1, 2
    ORDER BY pipeline_revenue DESC
    """

def get_owner_performance() -> str:
    """
    Owner Performance Matrix.
    """
    return """
    SELECT
      COALESCE(owner_code, 'Unassigned') AS owner_name,
      COALESCE(closure_probability, 'Unknown') AS win_probability,
      COUNT(*) AS active_deals,
      SUM(COALESCE(TRY_CAST(masked_deal_value AS DOUBLE), 0)) AS pipeline_value
    FROM deals
    WHERE deal_status != 'Won' AND deal_status != 'Lost'
    GROUP BY 1, 2
    ORDER BY pipeline_value DESC
    LIMIT 20
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
    "yield_by_sector",
    "owner_leaderboard",
    "client_concentration",
    "volume_fulfillment",
    "deal_size_distribution",
    "revenue_leakage",
    "execution_velocity",
    "predictive_pipeline",
    "owner_performance"
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
        "yield_by_sector": get_yield_by_sector,
        "owner_leaderboard": get_owner_leaderboard,
        "client_concentration": get_client_concentration,
        "volume_fulfillment": get_volume_fulfillment,
        "deal_size_distribution": get_deal_size_distribution,
        "revenue_leakage": get_revenue_leakage,
        "execution_velocity": get_execution_velocity,
        "predictive_pipeline": get_predictive_pipeline,
        "owner_performance": get_owner_performance,
    }
    
    if query_type not in queries:
        raise ValueError(f"Unknown query type: {query_type}. Valid types: {list(queries.keys())}")
    
    return queries[query_type]()
