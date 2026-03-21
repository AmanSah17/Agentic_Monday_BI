"""
Table metadata catalog for Deals and Work Orders.
Defines: column types, date ranges, business metrics, null patterns.
Used by: query_validator, analytics endpoints, frontend schema displays.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class DateColumn:
    name: str
    description: str
    min_date: str  # "YYYY-MM-DD"
    max_date: str
    null_count: int
    

@dataclass
class ValueColumn:
    name: str
    description: str
    dtype: str
    min_value: float | None
    max_value: float | None
    null_count: int


@dataclass
class StatusEnumColumn:
    name: str
    description: str
    valid_values: list[str]
    null_count: int


@dataclass
class TableMetadata:
    table_name: str
    row_count: int
    date_columns: list[DateColumn]
    value_columns: list[ValueColumn]
    status_columns: list[StatusEnumColumn]
    all_columns: list[str]
    
    def get_column_info(self, col_name: str) -> dict[str, Any]:
        """Retrieve metadata for a specific column."""
        for dc in self.date_columns:
            if dc.name == col_name:
                return {"type": "date", "data": dc}
        for vc in self.value_columns:
            if vc.name == col_name:
                return {"type": "value", "data": vc}
        for sc in self.status_columns:
            if sc.name == col_name:
                return {"type": "status", "data": sc}
        return {"type": "unknown", "data": None}


# DEALS TABLE METADATA
DEALS_METADATA = TableMetadata(
    table_name="deals",
    row_count=346,
    date_columns=[
        DateColumn(
            name="created_date",
            description="Date deal was created in system",
            min_date="2024-08-30",
            max_date="2025-12-26",
            null_count=3,
        ),
        DateColumn(
            name="created_at",
            description="System timestamp when deal record was created",
            min_date="2026-03-20",
            max_date="2026-03-20",
            null_count=0,
        ),
        DateColumn(
            name="updated_at",
            description="System timestamp of last update",
            min_date="2026-03-20",
            max_date="2026-03-20",
            null_count=0,
        ),
        DateColumn(
            name="tentative_close_date",
            description="Projected close date for deal",
            min_date="2024-09-30",
            max_date="2026-03-20",
            null_count=76,
        ),
        DateColumn(
            name="close_date_a",
            description="Actual close date (populated only for closed deals)",
            min_date="2024-09-30",
            max_date="2024-09-30",
            null_count=320,
        ),
    ],
    value_columns=[
        ValueColumn(
            name="masked_deal_value",
            description="Deal value in currency (masked for privacy)",
            dtype="float64",
            min_value=305850.0,
            max_value=305850000.0,
            null_count=181,
        ),
        ValueColumn(
            name="closure_probability",
            description="Estimated win probability (0-100, if available)",
            dtype="float64",
            min_value=0.0,
            max_value=100.0,
            null_count=258,
        ),
    ],
    status_columns=[
        StatusEnumColumn(
            name="deal_stage",
            description="Current stage in sales pipeline",
            valid_values=[
                "A. Prospecting",
                "B. Sales Qualified Leads",
                "C. Proposal/Invoice Sent",
                "D. Feasibility",
                "E. Proposal/Commercials Sent",
                "M. Projects On Hold",
            ],
            null_count=0,
        ),
        StatusEnumColumn(
            name="deal_status",
            description="Overall deal status",
            valid_values=["Open", "On Hold", "Lost", "Won"],
            null_count=1,
        ),
    ],
    all_columns=[  # 28 total columns
        "item_id",                      # 1. Unique deal identifier
        "item_name",                    # 2. Deal name/title
        "created_at",                   # 3. System creation timestamp
        "updated_at",                   # 4. Last system update
        "group_id",                     # 5. Category ID
        "group_title",                  # 6. Category name
        "owner_code",                   # 7. Sales owner identifier
        "owner_code__raw",              # 8. Raw Monday.com owner data (JSON)
        "client_code",                  # 9. Client/Company identifier
        "client_code__raw",             # 10. Raw Monday.com client data (JSON)
        "deal_status",                  # 11. Status: Open/On Hold/Won/Lost
        "deal_status__raw",             # 12. Raw Monday.com status data (JSON)
        "close_date_a",                 # 13. Deal closure date
        "close_date_a__raw",            # 14. Raw Monday.com close date (JSON)
        "closure_probability",          # 15. Win probability (High/Medium/Low)
        "closure_probability__raw",     # 16. Raw Monday.com probability (JSON)
        "masked_deal_value",            # 17. Deal value in currency (₹)
        "masked_deal_value__raw",       # 18. Raw Monday.com value (JSON)
        "tentative_close_date",         # 19. Projected closure date
        "tentative_close_date__raw",    # 20. Raw Monday.com tentative date (JSON)
        "deal_stage",                   # 21. Pipeline stage (A-M)
        "deal_stage__raw",              # 22. Raw Monday.com stage (JSON)
        "product_deal",                 # 23. Product/service type
        "product_deal__raw",            # 24. Raw Monday.com product (JSON)
        "sectorservice",                # 25. Sector (Mining/Powerline/Renewables/Tender)
        "sectorservice__raw",           # 26. Raw Monday.com sector (JSON)
        "created_date",                 # 27. Deal creation date
        "created_date__raw",            # 28. Raw Monday.com creation date (JSON)
    ],
)


# WORK ORDERS TABLE METADATA
WORK_ORDERS_METADATA = TableMetadata(
    table_name="work_orders",
    row_count=176,
    date_columns=[
        DateColumn(
            name="created_at",
            description="System timestamp when work order was created",
            min_date="2026-03-20",
            max_date="2026-03-20",
            null_count=0,
        ),
        DateColumn(
            name="updated_at",
            description="System timestamp of last update",
            min_date="2026-03-20",
            max_date="2026-03-20",
            null_count=0,
        ),
        DateColumn(
            name="probable_start_date",
            description="Expected work start date",
            min_date="2025-05-01",
            max_date="2026-04-30",
            null_count=18,
        ),
        DateColumn(
            name="probable_end_date",
            description="Expected work completion date",
            min_date="2025-05-01",
            max_date="2026-04-30",
            null_count=19,
        ),
        DateColumn(
            name="data_delivery_date",
            description="Expected date for project deliverables",
            min_date="2025-05-01",
            max_date="2026-01-14",
            null_count=118,
        ),
        DateColumn(
            name="date_of_poloi",
            description="Date of Principal Officer Letter of Intent",
            min_date="2025-05-01",
            max_date="2025-10-29",
            null_count=1,
        ),
        DateColumn(
            name="last_invoice_date",
            description="Last billing date for this work order",
            min_date="2025-07-18",
            max_date="2026-01-14",
            null_count=89,
        ),
    ],
    value_columns=[
        ValueColumn(
            name="amount_in_rupees_excl_of_gst_masked",
            description="Total project value excluding GST",
            dtype="float64",
            min_value=135652.0,
            max_value=3995568.0,
            null_count=1,
        ),
        ValueColumn(
            name="amount_in_rupees_incl_of_gst_masked",
            description="Total project value including GST",
            dtype="float64",
            min_value=160069.36,
            max_value=4714770.24,
            null_count=0,
        ),
        ValueColumn(
            name="billed_value_in_rupees_excl_of_gst_masked",
            description="Amount billed to customer (excl. GST)",
            dtype="float64",
            min_value=0.0,
            max_value=1433885.902,
            null_count=63,
        ),
        ValueColumn(
            name="billed_value_in_rupees_incl_of_gst_masked",
            description="Amount billed to customer (incl. GST)",
            dtype="float64",
            min_value=0.0,
            max_value=1433885.902,
            null_count=0,
        ),
        ValueColumn(
            name="collected_amount_in_rupees_incl_of_gst_masked",
            description="Amount actually collected from customer",
            dtype="float64",
            min_value=0.0,
            max_value=1433885.902,
            null_count=98,
        ),
        ValueColumn(
            name="amount_receivable_masked",
            description="Outstanding receivables",
            dtype="float64",
            min_value=0.0,
            max_value=2916764.64,
            null_count=None,
        ),
    ],
    status_columns=[
        StatusEnumColumn(
            name="execution_status",
            description="Current execution status of work order",
            valid_values=[
                "Not Started",
                "In Progress",
                "On Hold",
                "Completed",
                "Executed until current month",
            ],
            null_count=4,
        ),
        StatusEnumColumn(
            name="document_type",
            description="Type of engagement document",
            valid_values=["Purchase Order", "LOA/LOI"],
            null_count=14,
        ),
        StatusEnumColumn(
            name="invoice_status",
            description="Billing status of work order",
            valid_values=[
                "Not billed yet",
                "Partially Billed",
                "BIlled",
                "Fully Billed",
            ],
            null_count=None,
        ),
        StatusEnumColumn(
            name="collection_status",
            description="Payment collection status",
            valid_values=["Open", "Closed"],
            null_count=None,
        ),
        StatusEnumColumn(
            name="billing_status",
            description="Overall billing workflow status",
            valid_values=["Update Required", "Open", "Partially Billed", "BIlled"],
            null_count=None,
        ),
    ],
    all_columns=[
        "item_id",
        "item_name",
        "created_at",
        "updated_at",
        "group_id",
        "group_title",
        "customer_name_code",
        "serial_",
        "nature_of_work",
        "last_executed_month_of_recurring_project",
        "execution_status",
        "data_delivery_date",
        "date_of_poloi",
        "document_type",
        "probable_start_date",
        "probable_end_date",
        "bdkam_personnel_code",
        "sector",
        "type_of_work",
        "is_any_skylark_software_platform_part_of_the_client_deliverables_in_this_deal",
        "last_invoice_date",
        "latest_invoice_no",
        "amount_in_rupees_excl_of_gst_masked",
        "amount_in_rupees_incl_of_gst_masked",
        "billed_value_in_rupees_excl_of_gst_masked",
        "billed_value_in_rupees_incl_of_gst_masked",
        "collected_amount_in_rupees_incl_of_gst_masked",
        "amount_to_be_billed_in_rs_exl_of_gst_masked",
        "amount_to_be_billed_in_rs_incl_of_gst_masked",
        "amount_receivable_masked",
        "ar_priority_account",
        "quantity_by_ops",
        "quantities_as_per_po",
        "quantity_billed_till_date",
        "balance_in_quantity",
        "invoice_status",
        "expected_billing_month",
        "actual_billing_month",
        "actual_collection_month",
        "wo_status_billed",
        "collection_status",
        "collection_date",
        "billing_status",
    ],
)


def get_table_metadata(table_name: str) -> TableMetadata:
    """Retrieve metadata for a table by name."""
    if table_name.lower() == "deals":
        return DEALS_METADATA
    elif table_name.lower() == "work_orders":
        return WORK_ORDERS_METADATA
    raise ValueError(f"Unknown table: {table_name}")


def get_all_metadata() -> dict[str, TableMetadata]:
    """Return metadata for all tables."""
    return {
        "deals": DEALS_METADATA,
        "work_orders": WORK_ORDERS_METADATA,
    }
