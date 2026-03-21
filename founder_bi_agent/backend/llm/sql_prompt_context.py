"""
SQL Generation System Prompt and Context Builder
Provides comprehensive schema context to LLMs for accurate SQL generation.
Works with REAL Monday.com data from Excel exports (Deals and Work Orders boards).
Updated: March 21, 2026 - Calibrated against actual data structures
"""

from typing import Dict, Any

SYSTEM_PROMPT_SQL_GENERATION = """You are an expert DuckDB SQL analyst working with Monday.com business data.

⚠️ CRITICAL DATA STRUCTURE FACTS (REAL DATA FROM EXCEL EXPORTS):

TABLE 1: DEALS (Deal funnel Data.xlsx)
- 346 rows, 12 columns
- Columns: Deal Name, Owner code, Client Code, Deal Status, Close Date (A), Closure Probability, 
  Masked Deal value, Tentative Close Date, Deal Stage, Product deal, Sector/service, Created Date

TABLE 2: WORK_ORDERS (Work_Order_Tracker Data.xlsx)
- 176 rows, 38 columns
- Key columns: Deal name masked, Sector, Execution Status, Nature of Work, WO Status (billed), 
  Billing Status, Amount in Rupees (Excl of GST) (Masked), and 31 additional fields

🔗 JOIN KEY: Deals.'Deal Name' = Work_Orders.'Deal name masked'

COLUMN NAME MAPPING (EXACT NAMES - Case Sensitive):
Deals Table:
  ✓ "Deal Name" (string, 155 unique values)
  ✓ "Owner code" (string, 7 values: OWNER_001-OWNER_007)
  ✓ "Client Code" (string, 199 unique values)
  ✓ "Deal Status" (string, 5 values: Open, On Hold, Dead, Won, Deal Status)
  ✓ "Deal Stage" (string, 17 values: B. Sales Qualified Leads, E. Proposal/Commercials Sent, etc.)
  ✓ "Sector/service" (string, 12 values: Mining, Powerline, Tender, Renewables, DSP, Railways, etc.)
  ✓ "Masked Deal value" (float, range: ₹51K - ₹751M, 47.7% populated)
  ✓ "Created Date" (date, range: 2024-08-09 to 2026-01-09)
  ✓ "Close Date (A)" (date, range: 2024-12-31 to 2026-01-15, 8.1% populated)
  ✓ "Tentative Close Date" (date, 78.6% populated)
  ✓ "Closure Probability" (string, 4 values: High, Medium, Low)
  ✓ "Product deal" (string, 10 types: Service + Spectra, Pure Service, Hardware, etc.)

Work Orders Table:
  ✓ "Deal name masked" (string, 58 unique - JOIN TO DEALS)
  ✓ "Sector" (string, 6 values: Mining, Powerline, Renewables, Railways, Construction, Others)
  ✓ "Execution Status" (string, 7 values: Completed, Not Started, Executed until current month, Ongoing, Pause/struck, Partial Completed)
  ✓ "Nature of Work" (string, 4 types: One time Project, Recurring Project, Support Activity, Others)
  ✓ "WO Status (billed)" (string, 2 values: Open, Closed)
  ✓ "Billing Status" (string, 5 values: Update Required, Partially Billed, Billed, Not Billable, Stuck)
  ✓ "Amount in Rupees (Excl of GST) (Masked)" (float, 99.4% populated)
  ✓ "Type of Work" (string, Powerline Inspection, Volumetric survey, Topography Survey, etc.)
  ✓ "Date of PO/LOI" (date, range: 2022-09-29 to 2026-01-12)
  ✓ "Probable Start Date" (date)
  ✓ "Probable End Date" (date)
  ✓ "Last invoice date" (date)

CATEGORICAL VALUE VALIDATION (DO NOT DEVIATE):
Sectors in Deals: Mining, Powerline, Tender, Renewables, DSP, Railways, Construction, Security and Surveillance, Others, Aviation, Manufacturing
Sectors in Work Orders: Mining, Powerline, Renewables, Railways, Construction, Others
⚠️ CRITICAL: Sector names may differ between tables - use context to map correctly
Deal Status Values: Open, On Hold, Dead, Won (plus header string "Deal Status" - exclude)
Deal Stage Values (17 unique): B. Sales Qualified Leads, E. Proposal/Commercials Sent, D. Feasibility, M. Projects On Hold, H. Work Order Received, F. Negotiations, C. Demo Done, A. Lead Generated, N. Not relevant, L. Project Lost, O. Not Relevant at all, J. Invoice sent, I. POC, G. Project Won, Project Completed, K. Amount Accrued
Execution Status: Completed, Not Started, Executed until current month, Ongoing, Pause/struck, Partial Completed, Details pending from Client
Billing Status: Update Required, Partially Billed, Billed, Not Billable, Stuck

DATABASE-SPECIFIC RULES (DuckDB):
- Use TRY_CAST() for all type conversions: TRY_CAST(column AS FLOAT), TRY_CAST(column AS DATE)
- Date/Timestamp handling: CAST(column AS DATE) for date comparisons
- Column names with spaces: Use double quotes: "Deal Name", "Masked Deal value", "Amount in Rupees (Excl of GST) (Masked)"
- Null handling: COALESCE(column, 'Unknown') for categoricals, NULL for numerics
- String matching: TRIM() and LOWER() for case-insensitive comparisons
- Aggregation: ALWAYS include ALL non-aggregated columns in GROUP BY

COMMON PATTERNS FOR THIS DATA:

-- Join deals with work orders
SELECT d."Deal Name", d."Sector/service", COUNT(wo."Deal name masked") as wo_count
FROM deals d
LEFT JOIN work_orders wo ON d."Deal Name" = wo."Deal name masked"
GROUP BY d."Deal Name", d."Sector/service"

-- Deal value by sector
SELECT "Sector/service", COUNT(*) as deal_count, SUM("Masked Deal value") as total_value
FROM deals
WHERE "Sector/service" IN ('Mining', 'Powerline', 'Renewables', 'Tender')
GROUP BY "Sector/service"

-- Work order status analysis
SELECT "Execution Status", "Billing Status", COUNT(*) as wo_count, SUM("Amount in Rupees (Excl of GST) (Masked)") as total_amount
FROM work_orders
GROUP BY "Execution Status", "Billing Status"

-- Date range filtering
WHERE CAST("Created Date" AS DATE) >= '2026-01-01' AND CAST("Created Date" AS DATE) <= '2026-03-31'

INSTRUCTIONS FOR THIS QUERY:
- Return ONLY valid DuckDB SQL (no markdown, no ```sql blocks)
- Reference ONLY columns listed above
- Use exact column names with quotes for names containing spaces
- Use TRY_CAST() for type safety
- Always GROUP BY all non-aggregated columns when using aggregate functions
- Validate categorical values before filtering
- For joins: use "Deal Name" in Deals as the join key to "Deal name masked" in Work Orders
- Limit results to 10,000 rows to prevent memory issues
"""


TABLE_METADATA_CONTEXT = {
    "Deals": {
        "source": "Deal funnel Data.xlsx",
        "row_count": 346,
        "description": "Sales pipeline and deal tracking data",
        "columns": {
            "Deal Name": {
                "type": "string",
                "description": "Deal identifier/name (155 unique values)",
                "sample_values": ["Naruto", "Scooby-Doo", "Appa", "Sakura"],
                "nullable": True,
                "join_key": True,
                "note": "Use this to JOIN with Work_Orders.'Deal name masked'"
            },
            "Owner code": {
                "type": "string",
                "description": "Sales owner/representative (7 values)",
                "values": ["OWNER_001", "OWNER_002", "OWNER_003", "OWNER_004", "OWNER_005", "OWNER_006", "OWNER_007"],
                "nullable": True
            },
            "Client Code": {
                "type": "string",
                "description": "Client/company identifier (199 unique values)",
                "sample_values": ["COMPANY089", "COMPANY001"],
                "nullable": True
            },
            "Deal Status": {
                "type": "string",
                "description": "Deal status/outcome (5 values)",
                "values": ["Open", "On Hold", "Dead", "Won"],
                "note": "May include header value 'Deal Status' - filter if needed",
                "nullable": True,
                "data_quality": "345/346 populated (99.7%)"
            },
            "Deal Stage": {
                "type": "string",
                "description": "Sales pipeline stage (17 values)",
                "values": [
                    "A. Lead Generated",
                    "B. Sales Qualified Leads",
                    "C. Demo Done",
                    "D. Feasibility",
                    "E. Proposal/Commercials Sent",
                    "F. Negotiations",
                    "G. Project Won",
                    "H. Work Order Received",
                    "I. POC",
                    "J. Invoice sent",
                    "K. Amount Accrued",
                    "L. Project Lost",
                    "M. Projects On Hold",
                    "N. Not relevant at the moment",
                    "O. Not Relevant at all",
                    "Project Completed"
                ],
                "nullable": False,
                "data_quality": "346/346 populated (100%)"
            },
            "Sector/service": {
                "type": "string",
                "description": "Business sector/service type (12 values)",
                "values": [
                    "Mining",
                    "Powerline",
                    "Tender",
                    "Renewables",
                    "DSP",
                    "Railways",
                    "Construction",
                    "Security and Surveillance",
                    "Others",
                    "Aviation",
                    "Manufacturing"
                ],
                "note": "CRITICAL: Column name includes forward slash '/'. Use quotes: \"Sector/service\"",
                "nullable": True,
                "data_quality": "338/346 populated (97.7%)"
            },
            "Masked Deal value": {
                "type": "float",
                "description": "Deal value in ₹ (privacy-masked)",
                "min": 51440,
                "max": 751473450,
                "mean": 13972837,
                "median": 1101060,
                "total": 2305518041,
                "nullable": True,
                "data_quality": "165/346 populated (47.7%)"
            },
            "Closure Probability": {
                "type": "string",
                "description": "Win probability/likelihood (4 values)",
                "values": ["High", "Medium", "Low"],
                "nullable": True,
                "data_quality": "88/346 populated (25.4%)"
            },
            "Created Date": {
                "type": "date",
                "description": "Deal creation date (string format in Excel)",
                "min": "2024-08-09",
                "max": "2026-01-09",
                "note": "Convert with CAST(\"Created Date\" AS DATE)",
                "nullable": True,
                "data_quality": "345/346 populated (99.7%)"
            },
            "Close Date (A)": {
                "type": "date",
                "description": "Actual close date",
                "min": "2024-12-31",
                "max": "2026-01-15",
                "nullable": True,
                "data_quality": "28/346 populated (8.1%)"
            },
            "Tentative Close Date": {
                "type": "date",
                "description": "Projected/tentative close date",
                "nullable": True,
                "data_quality": "272/346 populated (78.6%)"
            },
            "Product deal": {
                "type": "string",
                "description": "Product/service type (10 values)",
                "values": [
                    "Service + Spectra",
                    "Pure Service",
                    "Spectra + DMO",
                    "Hardware",
                    "Dock + DMO + Spectra + Service",
                    "Dock + Spectra + Service",
                    "Dock + DMO + Spectra",
                    "Dock + DMO",
                    "Spectra Deal"
                ],
                "nullable": True,
                "data_quality": "176/346 populated (50.9%)"
            }
        },
        "date_range": {
            "created_date_min": "2024-08-09",
            "created_date_max": "2026-01-09"
        }
    },
    "work_orders": {
        "source": "Work_Order_Tracker Data.xlsx",
        "sheet": "work order tracker (header in row 2)",
        "row_count": 176,
        "column_count": 38,
        "description": "Work order execution, billing, and collection tracking",
        "key_columns": {
            "Deal name masked": {
                "type": "string",
                "description": "Deal identifier - matches Deals.'Deal Name'",
                "sample_values": ["Scooby-Doo", "Appa", "Sakura"],
                "unique_values": 58,
                "nullable": True,
                "join_key": True,
                "data_quality": "175/176 populated (99.4%)"
            },
            "Sector": {
                "type": "string",
                "description": "Business sector (6 values)",
                "values": ["Mining", "Powerline", "Renewables", "Railways", "Construction", "Others"],
                "note": "Different from Deals.'Sector/service' - may have different values",
                "nullable": False,
                "data_quality": "176/176 populated (100%)"
            },
            "Execution Status": {
                "type": "string",
                "description": "Work order execution status (7 values)",
                "values": [
                    "Completed",
                    "Not Started",
                    "Executed until current month",
                    "Ongoing",
                    "Pause / struck",
                    "Partial Completed",
                    "Details pending from Client"
                ],
                "nullable": True,
                "data_quality": "172/176 populated (97.7%)",
                "most_common": "Completed"
            },
            "Nature of Work": {
                "type": "string",
                "description": "Work order type (4 values)",
                "values": [
                    "One time Project",
                    "Recurring Project",
                    "Support Activity",
                    "Others"
                ],
                "nullable": True,
                "data_quality": "164/176 populated (93.2%)"
            },
            "WO Status (billed)": {
                "type": "string",
                "description": "Billing status (2 values)",
                "values": ["Open", "Closed"],
                "nullable": True,
                "data_quality": "102/176 populated (58.0%)"
            },
            "Billing Status": {
                "type": "string",
                "description": "Current billing status (5 values)",
                "values": [
                    "Update Required",
                    "Partially Billed",
                    "BIlled",
                    "Not Billable",
                    "Stuck"
                ],
                "note": "Note typo: 'BIlled' vs 'Billed' - use LOWER() for matching",
                "nullable": True,
                "data_quality": "28/176 populated (15.9%)"
            },
            "Amount in Rupees (Excl of GST) (Masked)": {
                "type": "float",
                "description": "WO amount in ₹ (excluding GST, privacy-masked)",
                "min": 72525,
                "max": 7890567,
                "total": 211649409,
                "mean": 1209425,
                "median": 308300,
                "nullable": True,
                "data_quality": "175/176 populated (99.4%)",
                "note": "Use quotes for full column name"
            },
            "Type of Work": {
                "type": "string",
                "description": "Specific work type/classification",
                "sample_values": [
                    "Powerline Inspection",
                    "Volumetric survey",
                    "Topography Survey: RGB",
                    "Hydrology"
                ],
                "nullable": True
            },
            "Date of PO/LOI": {
                "type": "date",
                "description": "PO or Letter of Intent date",
                "min": "2022-09-29",
                "max": "2026-01-12",
                "nullable": True
            },
            "Probable Start Date": {
                "type": "date",
                "description": "Projected work start date",
                "min": "2024-07-30",
                "max": "2026-01-19",
                "nullable": True
            },
            "Probable End Date": {
                "type": "date",
                "description": "Projected work completion date",
                "min": "2025-04-10",
                "max": "2028-03-31",
                "nullable": True
            },
            "Last invoice date": {
                "type": "date",
                "description": "Date of most recent invoice",
                "min": "2025-03-31",
                "max": "2026-01-14",
                "nullable": True
            },
            "Expected Billing Month": {
                "type": "string",
                "description": "Expected billing month (e.g., Jan 2026)",
                "nullable": True
            },
            "Actual Billing Month": {
                "type": "string",
                "description": "Actual billing month",
                "nullable": True
            },
            "Actual Collection Month": {
                "type": "string",
                "description": "Actual collection month",
                "nullable": True
            }
        },
        "additional_columns": [
            "Customer Name Code",
            "Serial #",
            "Last executed month of recurring project",
            "Document Type",
            "BD/KAM Personnel code",
            "Is any Skylark software platform part of the client deliverables",
            "Latest invoice no.",
            "Amount in Rupees (Incl of GST) (Masked)",
            "Billed Value in Rupees (Excl of GST.) (Masked)",
            "Billed Value in Rupees (Incl of GST.) (Masked)",
            "Collected Amount in Rupees (Incl of GST.) (Masked)",
            "Amount to be billed in Rs. (Exl. of GST) (Masked)",
            "Amount to be billed in Rs. (Incl. of GST) (Masked)",
            "Amount Receivable (Masked)",
            "AR Priority account",
            "Quantity by Ops",
            "Quantities as per PO",
            "Quantity billed (till date)",
            "Balance in quantity",
            "Invoice Status",
            "Collection status",
            "Collection Date"
        ],
        "note": "Sheet has 38 columns total; see additional_columns for less-frequently-used fields"
    }
}

def create_schema_context_for_sql(table_schemas: Dict[str, Any] = None) -> str:
    """Combine system prompt with specific table schema for LLM context"""
    return SYSTEM_PROMPT_SQL_GENERATION + "\n\nACTUAL TABLE STRUCTURE:\n" + str(TABLE_METADATA_CONTEXT)

def create_validation_hint() -> str:
    """Create a hint for validating generated SQL against real data"""
    return """
SQL VALIDATION CHECKLIST (REAL DATA):
☐ Column names match EXACTLY (case-sensitive, with spaces in quotes)
  ✓ "Deal Name", "Owner code", "Client Code", "Deal Status", "Deal Stage"
  ✓ "Sector/service" (includes forward slash)
  ✓ "Masked Deal value", "Created Date", "Tentative Close Date"
  ✓ "Deal name masked", "Execution Status", "Billing Status"
  ✓ "Amount in Rupees (Excl of GST) (Masked)" (long name with parentheses)
☐ Categorical values are valid:
  ✓ Sectors (Deals): Mining, Powerline, Tender, Renewables, DSP, Railways, Construction, Security and Surveillance, Others, Aviation, Manufacturing
  ✓ Sectors (WO): Mining, Powerline, Renewables, Railways, Construction, Others
  ✓ Deal Status: Open, On Hold, Dead, Won
  ✓ Execution Status: Completed, Not Started, Executed until current month, Ongoing, Pause/struck, Partial Completed, Details pending
  ✓ Billing Status: Update Required, Partially Billed, BIlled, Not Billable, Stuck
☐ Join key is correct: Deals."Deal Name" = WorkOrders."Deal name masked"
☐ Date columns use CAST(column AS DATE) not string comparison
☐ Numeric columns use TRY_CAST(column AS FLOAT) for aggregation
☐ GROUP BY includes all non-aggregated columns
☐ No assumptions about missing data (use COALESCE for nulls)
☐ Results limited to appropriate size (avoid SELECT * on 38-column WO table)
"""
