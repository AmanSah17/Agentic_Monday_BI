from __future__ import annotations

from typing import Iterable

import pandas as pd


def generate_sql_heuristic(question: str, available_tables: Iterable[str]) -> str:
    q = question.lower()
    tables = list(available_tables)

    if ("column names" in q or "columns" in q or "schema" in q) and (
        "deals" in tables or "work_orders" in tables
    ):
        return """
        SELECT
            table_name,
            column_name
        FROM information_schema.columns
        WHERE table_name IN ('deals', 'work_orders')
        ORDER BY table_name, ordinal_position
        """

    if "how many tables" in q and "deals" in tables and "work_orders" in tables:
        return """
        SELECT
          'deals' AS table_name,
          COUNT(*) AS row_count
        FROM deals
        UNION ALL
        SELECT
          'work_orders' AS table_name,
          COUNT(*) AS row_count
        FROM work_orders
        """

    if (
        ("time horizon" in q or "date range" in q or "temporal range" in q)
        and "deals" in tables
        and "work_orders" in tables
    ):
        return """
        SELECT
          MIN(event_date) AS min_date,
          MAX(event_date) AS max_date
        FROM (
          SELECT created_at::DATE AS event_date FROM deals WHERE created_at IS NOT NULL
          UNION ALL
          SELECT updated_at::DATE AS event_date FROM deals WHERE updated_at IS NOT NULL
          UNION ALL
          SELECT created_at::DATE AS event_date FROM work_orders WHERE created_at IS NOT NULL
          UNION ALL
          SELECT updated_at::DATE AS event_date FROM work_orders WHERE updated_at IS NOT NULL
        ) AS all_dates
        """

    if "deals" in tables and "pipeline" in q and "sector" in q:
        return """
        SELECT
            COALESCE(sectorservice, 'Unknown') AS sector,
            COUNT(*) AS deals_count,
            SUM(COALESCE(masked_deal_value, 0)) AS pipeline_value
        FROM deals
        GROUP BY 1
        ORDER BY pipeline_value DESC
        LIMIT 25
        """

    if "deals" in tables and "pipeline" in q:
        return """
        SELECT
            COALESCE(deal_stage, 'Unknown') AS deal_stage,
            COUNT(*) AS deals_count,
            SUM(COALESCE(masked_deal_value, 0)) AS pipeline_value
        FROM deals
        GROUP BY 1
        ORDER BY pipeline_value DESC
        LIMIT 25
        """

    if "deals" in tables and ("deal stage" in q or "stage" in q):
        return """
        SELECT
            COALESCE(deal_stage, 'Unknown') AS deal_stage,
            COUNT(*) AS deals_count
        FROM deals
        GROUP BY 1
        ORDER BY deals_count DESC
        LIMIT 25
        """

    if "work_orders" in tables and ("receivable" in q or "amount receivable" in q):
        return """
        SELECT
            SUM(COALESCE(amount_receivable_masked, 0)) AS total_amount_receivable
        FROM work_orders
        """

    if "work_orders" in tables and "billed" in q and "collected" in q and "sector" in q:
        return """
        SELECT
            COALESCE(sector, 'Unknown') AS sector,
            SUM(COALESCE(billed_value_in_rupees_incl_of_gst_masked, 0)) AS billed_value,
            SUM(COALESCE(collected_amount_in_rupees_incl_of_gst_masked, 0)) AS collected_value
        FROM work_orders
        GROUP BY 1
        ORDER BY billed_value DESC
        """

    if "work_orders" in tables and ("work order" in q or "delivery" in q):
        return """
        SELECT
            COALESCE(execution_status, 'Unknown') AS execution_status,
            COUNT(*) AS work_order_count
        FROM work_orders
        GROUP BY 1
        ORDER BY work_order_count DESC
        """

    first_table = tables[0] if tables else "deals"
    return f"SELECT * FROM {first_table} LIMIT 50000"


def build_schema_hint(tables: dict[str, pd.DataFrame]) -> str:
    lines: list[str] = []
    for table_name, df in tables.items():
        cols = ", ".join(f"{c}:{str(df[c].dtype)}" for c in df.columns[:40])
        lines.append(f"- {table_name}({cols})")
    return "\n".join(lines)
