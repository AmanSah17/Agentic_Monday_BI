# SQL Generation & Debugging Guide

## Common SQL Generation Issues & Fixes

### Issue 1: Using `created_at` Instead of `created_date`
**Problem**: Queries fail with "unknown column: created_at"
```sql
-- ❌ WRONG
SELECT * FROM deals WHERE created_at >= '2026-01-01'

-- ✅ CORRECT
SELECT * FROM deals WHERE TRY_CAST(created_date AS DATE) >= TRY_CAST('2026-01-01' AS DATE)
```
**Why**: The Monday.com data exports `created_date` as DATE type, not `created_at` as timestamp.

---

### Issue 2: PostgreSQL Syntax in DuckDB Queries
**Problem**: "Did not specify a type" errors when using `::`
```sql
-- ❌ WRONG (PostgreSQL syntax)
SELECT COUNT(*) FROM deals WHERE created_at::DATE >= '2026-01-01'

-- ✅ CORRECT (DuckDB syntax)
SELECT COUNT(*) FROM deals WHERE TRY_CAST(created_date AS DATE) >= TRY_CAST('2026-01-01' AS DATE)
```
**Why**: DuckDB uses `TRY_CAST()` for type conversions, not the `::` operator.

---

### Issue 3: Invalid Sector Values
**Problem**: "No data returned" when filtering by sector
```sql
-- ❌ WRONG - 'Railway' doesn't exist in the dataset
SELECT * FROM deals WHERE sectorservice = 'Railway'

-- ✅ CORRECT - Use only valid sectors
SELECT * FROM deals 
WHERE sectorservice IN ('Mining', 'Powerline', 'Renewables', 'Tender')
```
**Valid Sectors**: Mining, Powerline, Renewables, Tender
**Invalid**: Railway (commonly assumed but not present)

---

### Issue 4: Missing GROUP BY Clauses
**Problem**: Aggregation queries fail with "must aggregate all non-aggregated columns"
```sql
-- ❌ WRONG
SELECT sector, COUNT(*) FROM deals WHERE sector IS NOT NULL

-- ✅ CORRECT
SELECT sectorservice, COUNT(*) FROM deals 
WHERE sectorservice IS NOT NULL
GROUP BY sectorservice
```
**Rule**: All non-aggregated columns must appear in GROUP BY.

---

### Issue 5: Categorical Column Whitespace
**Problem**: Filters match nothing due to leading/trailing spaces
```sql
-- ❌ May fail due to whitespace
SELECT * FROM deals WHERE deal_stage = 'A. Prospecting'

-- ✅ Robust approach
SELECT * FROM deals WHERE TRIM(deal_stage) = TRIM('A. Prospecting')
```

---

## Table Schema Reference

### DEALS Table (346 rows)
**Date Range**: 2024-08-30 to 2025-12-26

| Column | Type | Valid Values | Notes |
|--------|------|--------------|-------|
| item_id | string | - | Unique deal ID |
| item_name | string | - | Deal name |
| created_date | **date** | - | **USE THIS, NOT created_at** |
| deal_stage | string | A. Prospecting, B. Sales Qualified Leads, C. Proposal/Invoice Sent, D. Feasibility, E. Proposal/Commercials Sent, M. Projects On Hold | Sales funnel stage |
| deal_status | string | Open, Won, Lost, On Hold | Deal outcome status |
| **sectorservice** | string | **Mining, Powerline, Renewables, Tender** | **NOT Railway** |
| masked_deal_value | float | 305,850 - 305,850,000 | Deal value in ₹ |
| owner_code | string | - | Sales owner ID |
| client_code | string | - | Client/company ID |
| closure_probability | string | High, Medium, Low | Win probability |

### WORK_ORDERS Table (176 rows)
**Date Range**: 2025-05-01 to 2026-04-30

| Column | Type | Notes |
|--------|------|-------|
| item_id | string | Unique work order ID |
| created_date | **date** | Work order creation date |
| execution_status | string | Status of work execution |
| billing_status | string | Status of billing |
| collection_status | string | Status of payment collection |
| project_value | float | Original project value |
| billed_value | float | Amount billed to customer |
| collected_value | float | Amount actually collected |

---

## DuckDB Syntax Cheatsheet

### Type Casting
```sql
-- Safe type casting with fallback to NULL
TRY_CAST(column AS DATE)
TRY_CAST(column AS FLOAT)
TRY_CAST(column AS INTEGER)
```

### Date Operations
```sql
-- Extract components
EXTRACT(YEAR FROM date_col)
EXTRACT(MONTH FROM date_col)
EXTRACT(DAY FROM date_col)

-- Date arithmetic
date_col + INTERVAL 30 DAY
date_col - INTERVAL 1 MONTH

-- Date formatting
STRFTIME(date_col, '%Y-%m-%d')
```

### Null Handling
```sql
-- Replace nulls
COALESCE(column, 'Unknown')
IFNULL(column, 0)  -- Numeric default
```

### String Operations
```sql
-- Trim whitespace
TRIM(column)
LTRIM(column)
RTRIM(column)

-- Case-insensitive matching
LOWER(column) = 'value'
ILIKE '%pattern%'  -- DuckDB's case-insensitive LIKE
```

### Aggregation
```sql
-- Always include GROUP BY for non-aggregated columns
SELECT sector, COUNT(*), SUM(value)
FROM deals
GROUP BY sector
ORDER BY SUM(value) DESC

-- Filtering on aggregates
HAVING COUNT(*) > 10
```

---

## Testing SQL Queries

### Step 1: Check Basic Schema
```sql
SELECT COUNT(*) FROM deals
SELECT COUNT(*) FROM work_orders
```

### Step 2: Check Date Range
```sql
SELECT MIN(created_date), MAX(created_date) FROM deals
SELECT MIN(created_date), MAX(created_date) FROM work_orders
```

### Step 3: Check Categorical Values
```sql
SELECT DISTINCT sectorservice FROM deals WHERE sectorservice IS NOT NULL
SELECT DISTINCT deal_stage FROM deals WHERE deal_stage IS NOT NULL
SELECT DISTINCT deal_status FROM deals WHERE deal_status IS NOT NULL
```

### Step 4: Test Aggregations
```sql
SELECT sectorservice, COUNT(*) 
FROM deals 
WHERE sectorservice IS NOT NULL
GROUP BY sectorservice
```

---

## Debugging LLM-Generated SQL

When SQL generation fails:

1. **Check the Fallback SQL**: The system logs `last_generation_meta` with the fallback query used
2. **Review the Error**: SQL execution errors are included in the insight output
3. **Validate Manually**: Run the simpler schema check queries above
4. **Check Assumptions**: 
   - Is the date column `created_date` or something else?
   - Are the categorical values exactly what the query expects?
   - Are there any null/empty strings that need special handling?

---

## Key Takeaways for LLM Integration

The system prompt (`SYSTEM_PROMPT_SQL_GENERATION`) emphasizes:
- ✅ Use `created_date` not `created_at`
- ✅ Use `TRY_CAST()` not `::`
- ✅ Use valid sectors: Mining, Powerline, Renewables, Tender (NOT Railway)
- ✅ Use `GROUP BY` for all non-aggregated columns
- ✅ Use `TRIM()` for categorical comparisons
- ✅ Validate dates in YYYY-MM-DD format

When these are violated, the fallback heuristic SQL takes over automatically.
