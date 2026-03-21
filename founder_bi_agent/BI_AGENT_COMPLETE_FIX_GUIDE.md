# BI Agent Data Pipeline - Complete Setup & Debugging Guide

## Overview
Your BI Agent ingests Monday.com data, generates SQL queries through LLMs, and provides business insights.

**Current Issues to Fix:**
1. ❌ SQL generation using wrong column names (`created_date` instead of `created_at`)
2. ❌ System returning raw SQL instead of executing it
3. ❌ No insights being generated
4. ❌ Raw data displays instead of analysis

---

## Part 1: Correct Column Reference

### The Root Issue
Monday.com GraphQL API returns **timestamps**, not dates:

```json
{
  "item_id": "2634233649",
  "item_name": "Naruto",
  "created_at": "2026-03-20T21:06:41+05:30",    // ← RFC3339 TIMESTAMP
  "updated_at": "2026-03-20T21:06:41+05:30",    // ← RFC3339 TIMESTAMP
  "group_id": "topics",
  "group_title": "Group Title"
  // + other custom columns
}
```

### ✅ CORRECT SQL for Q1 2026 Pipeline Analysis

```sql
-- Get deals created in Q1 2026 (Jan-Mar)
SELECT 
  DATE_TRUNC('day', created_at::TIMESTAMP) AS created_date,
  deal_stage,
  deal_status,
  COUNT(*) AS num_deals,
  SUM(COALESCE(TRY_CAST(masked_deal_value AS FLOAT), 0)) AS total_value
FROM 
  deals
WHERE 
  created_at::TIMESTAMP >= '2026-01-01T00:00:00Z'::TIMESTAMP
  AND created_at::TIMESTAMP < '2026-04-01T00:00:00Z'::TIMESTAMP
GROUP BY 
  DATE_TRUNC('day', created_at::TIMESTAMP),
  deal_stage,
  deal_status
ORDER BY 
  created_date DESC,
  total_value DESC
```

### ✅ CORRECT SQL for January 2026 Sales

```sql
-- Get sales made in January 2026 by sector
SELECT 
  sectorservice AS sector,
  COUNT(DISTINCT item_id) AS num_deals,
  SUM(COALESCE(TRY_CAST(masked_deal_value AS FLOAT), 0)) AS total_sales,
  AVG(COALESCE(TRY_CAST(masked_deal_value AS FLOAT), 0)) AS avg_deal_value,
  MAX(COALESCE(TRY_CAST(masked_deal_value AS FLOAT), 0)) AS largest_deal
FROM 
  deals
WHERE 
  created_at::TIMESTAMP >= '2026-01-01T00:00:00Z'::TIMESTAMP
  AND created_at::TIMESTAMP < '2026-02-01T00:00:00Z'::TIMESTAMP
  AND sectorservice IN ('Mining', 'Powerline', 'Renewables', 'Tender')
GROUP BY 
  sectorservice
ORDER BY 
  total_sales DESC
```

---

## Part 2: System Architecture & Execution Flow

### The Correct Pipeline (What Should Happen)

```
USER QUESTION
    ↓
[1] Intent Router → Determine if pipeline_health or general_bi
    ↓
[2] Clarifier → Ask for timeframe if missing
    ↓
[3] Schema Discovery → Fetch board schemas from Monday.com
    ↓
[4] Data Fetch Live → Query Monday.com API for deals and work_orders
    ↓
[5] Normalize Data → Clean column names, handle nulls
    ↓
[6] Quality Profiler → Analyze data for missing values, stats
    ↓
[7] Text2SQL Planner → Generate SQL with corrected schema
    ↓
[8] SQL Guardrail → Validate it's read-only
    ↓
[9] SQL Execute → Run query against DuckDB in-memory database
    ↓
[10] Insight Writer → Generate business summary (NOT raw data)
    ↓
[11] Viz Builder → Create chart if applicable
    ↓
BUSINESS INSIGHT + DATA + CHART
```

### Where It's Breaking

The issue is in **Step 7 (Text2SQL Planner)**:  
- ❌ System prompt assumes `created_date` column
- ❌ Actual data has `created_at` + custom columns
- ❌ LLM generates invalid SQL
- ❌ SQL execution fails
- ❌ Fallback returns raw data instead of insight

---

## Part 3: Data Schema - What Actually Exists

### Core Monday.com Fields (Always Present)

```
deals TABLE:
├── item_id: string (unique ID)
├── item_name: string (deal name)
├── created_at: TIMESTAMP RFC3339 (e.g., 2026-01-09T12:34:56+05:30)
├── updated_at: TIMESTAMP RFC3339
├── group_id: string
├── group_title: string
└── [CUSTOM COLUMNS from Monday.com board columns...]
    ├── deal_stage: string
    ├── deal_status: string
    ├── sectorservice: string
    ├── masked_deal_value: string (parsed as float)
    ├── owner_code: string
    ├── client_code: string
    ├── closure_probability: string
    └── (and _raw versions of each custom column)

work_orders TABLE:
├── item_id: string
├── item_name: string  
├── created_at: TIMESTAMP RFC3339
├── updated_at: TIMESTAMP RFC3339
├── group_id: string
├── group_title: string
└── [CUSTOM COLUMNS from Monday.com board columns...]
    ├── execution_status: string
    ├── billing_status: string
    ├── collection_status: string
    ├── project_value: string (parsed as float)
    ├── billed_value: string (parsed as float)
    ├── collected_value: string (parsed as float)
    └── (and _raw versions)
```

---

## Part 4: Testing Your SQL Locally

### Quick Schema Check

```bash
# Run these directly in DuckDB to verify columns
```

```sql
-- See what columns are actually in deals
DESCRIBE deals;

-- See what columns are actually in work_orders  
DESCRIBE work_orders;

-- Check timestamp format
SELECT created_at, updated_at FROM deals LIMIT 5;

-- Verify valid sectors actually exist
SELECT DISTINCT sectorservice FROM deals WHERE sectorservice IS NOT NULL;
```

### Test Query #1: Q1 2026 Pipeline

```sql
SELECT 
  sectorservice,
  deal_stage,
  COUNT(*) AS num_deals,
  TRY_CAST(SUM(masked_deal_value) AS FLOAT) AS total_value
FROM deals
WHERE created_at::TIMESTAMP >= '2026-01-01T00:00:00Z'::TIMESTAMP
  AND created_at::TIMESTAMP < '2026-04-01T00:00:00Z'::TIMESTAMP
GROUP BY sectorservice, deal_stage
ORDER BY total_value DESC
```

### Test Query #2: January 2026 Sales

```sql
SELECT 
  sectorservice,
  COUNT(*) AS deals_count,
  COUNT(DISTINCT owner_code) AS unique_owners,
  SUM(TRY_CAST(masked_deal_value AS FLOAT)) AS total_sales
FROM deals
WHERE created_at::TIMESTAMP >= '2026-01-01T00:00:00Z'::TIMESTAMP
  AND created_at::TIMESTAMP < '2026-02-01T00:00:00Z'::TIMESTAMP
GROUP BY sectorservice
ORDER BY total_sales DESC
```

---

## Part 5: System Prompt Update Required

**Location**: `founder_bi_agent/backend/llm/sql_prompt_context.py`

**What Changed:**
- ❌ OLD: told LLM to use `created_date` as DATE type
- ✅ NEW: tell LLM to use `created_at` as TIMESTAMP (RFC3339)

**Example in Prompt:**
```
DON'T:
  Use 'created_date' (type: date)

DO:
  Use 'created_at' (type: timestamp, RFC3339 format)
  Extract with: DATE_TRUNC('day', created_at::TIMESTAMP)
  Parse with: TRY_CAST(created_at AS TIMESTAMP)
```

---

## Part 6: Execute the Fix

### Step 1: Update Groq Client
File: `founder_bi_agent/backend/llm/groq_client.py`

The SQL generator should now use the corrected prompt that references timestamps, not dates.

### Step 2: Verify Heuristic SQL
File: `founder_bi_agent/backend/sql/sql_planner.py`

Fallback queries now use:
```sql
DATE_TRUNC('day', TRY_CAST(created_at AS TIMESTAMP))
```

Instead of:
```sql
TRY_CAST(created_date AS DATE)  -- WRONG
```

### Step 3: Test End-to-End

```bash
# Test the SQL prompt validation
python -m founder_bi_agent.backend.llm.test_sql_prompt_enhancements

# Run a test query through the API
python -c "
from founder_bi_agent.backend.service import FounderBIService
service = FounderBIService()
result = service.run_query('How many deals do we have in Q1 2026?')
print('ANSWER:', result['answer'])
print('SQL:', result['sql_query'])
print('ERROR:', result['sql_validation_error'])
"
```

---

## Part 7: Expected Output After Fix

### Before (Currently Broken)
```
SQL Generated:
SELECT * FROM deals WHERE created_date >= '2026-01-01'

Result Rows (1000s):
[raw data dump, no insights]

Error: Unknown column: created_date
```

### After (Fixed)
```
SQL Generated:
SELECT sectorservice, COUNT(*) as num_deals, SUM(masked_deal_value) as value
FROM deals
WHERE created_at::TIMESTAMP >= '2026-01-01T00:00:00Z'::TIMESTAMP
GROUP BY sectorservice

Answer (Insight):
"In Q1 2026, we have 87 deals in the pipeline valued at ₹2.1B. 
Mining leads with ₹800M (32%), followed by Renewables at ₹650M (25%). 
64% of deals are in prospecting phase, suggesting strong pipeline growth."

Chart:
[Bar chart: Sectors vs Deal Value]
```

---

## Part 8: Troubleshooting Checklist

- [ ] Prompt context uses `created_at` (not `created_date`)
- [ ] Prompt examples show timestamp handling
- [ ] Fallback SQL uses `DATE_TRUNC('day', created_at::TIMESTAMP)`
- [ ] Tests pass: `python -m test_sql_prompt_enhancements`
- [ ] Sample query returns insight (not raw SQL)
- [ ] Data displayed with business analysis (not data dump)
- [ ] Timestamps parsed correctly as RFC3339 format
- [ ] Sector filtering matches valid values

---

## Part 9: Key Files Updated

1. ✅ `sql_prompt_context.py` - Corrected prompt with timestamp guidance
2. ✅ `groq_client.py` - Integrated new prompt
3. ✅ `sql_planner.py` - Fixed heuristic SQL for timestamps
4. ✅ `SQL_GENERATION_GUIDE.md` - Updated documentation (timestamps)
5. ✅ `test_sql_prompt_enhancements.py` - Validation test suite

---

## Quick Reference: Wrong vs Right

| Issue | ❌ Wrong | ✅ Right |
|-------|----------|---------|
| Column name | `created_date` | `created_at` |
| Data type | DATE | TIMESTAMP (RFC3339) |
| Example | `2026-01-01` | `2026-01-09T12:34:56+05:30` |
| Extract date | `created_date` | `DATE_TRUNC('day', created_at::TIMESTAMP)` |
| Cast | `TRY_CAST(col AS DATE)` | `TRY_CAST(col AS TIMESTAMP)` |
| PostgreSQL syntax | `::` (sometimes fails) | `CAST()` or `TRY_CAST()` |
| Fallback query | Uses `created_date` | Uses `created_at` |
| Output | Raw SQL + raw data | Insight + analysis |
