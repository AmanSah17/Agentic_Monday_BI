# FounderBI Agent - Production System Architecture & Workflow

## Executive Summary

FounderBI is an **AI-powered Business Intelligence Research Agent** designed for executive decision-making. It operates as a deep research system that:

- **Automatically discovers and integrates** multi-source data (Monday.com boards, databases)
- **Understands complex business questions** in natural language
- **Generates intelligent SQL queries** to extract actionable insights
- **Summarizes findings** for executive consumption (CEO/CTO-level)
- **Delivers real-time analysis** without manual data engineering

---

## Part 1: Production Workflow Architecture

### Complete Data Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER QUESTION (CEO/CTO)                      │
│        "How is our pipeline doing in Q1 2026?"                  │
│        "What are top performing sectors by revenue?"            │
│        "Where are we losing deals and why?"                     │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [1] INTENT CLASSIFICATION                                        │
│ • Determine: Pipeline Health? Revenue? Operations? Forecasting? │
│ • Route to: Domain-specific analysis path                        │
│ • Risk Detection: Question validity, data gaps                   │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [2] CLARIFICATION ENGINE                                         │
│ • Identify missing context: Time periods, metrics, dimensions   │
│ • Ask precise follow-up: "Which quarter? Which sectors?"        │
│ • Validate assumptions: "Should we include lost deals?"         │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [3] DATA SOURCE DISCOVERY                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Monday.com Board Schema Inspection:                         │ │
│ │ • List all available boards (dealspipeline, workorders)     │ │
│ │ • Extract column definitions (deal_stage, value, etc.)      │ │
│ │ • Identify key metrics and dimensions                       │ │
│ │ • Map custom columns to business terms                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [4] LIVE DATA INGESTION                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Deals Table (deals):                                        │ │
│ │ • Fetch all items from deals board                          │ │
│ │ • Extract: item_id, item_name, created_at, custom columns  │ │
│ │ • Storage: In-memory DuckDB table (346 rows)                │ │
│ │                                                              │ │
│ │ Work Orders Table (work_orders):                            │ │
│ │ • Fetch all items from work_orders board                    │ │
│ │ • Extract: item_id, item_name, created_at, custom columns  │ │
│ │ • Storage: In-memory DuckDB table (176 rows)                │ │
│ │                                                              │ │
│ │ Custom Columns Discovered:                                  │ │
│ │ • deal_stage, deal_status, sectorservice, masked_deal_value│ │
│ │ • closure_probability, owner_code, client_code             │ │
│ │ • execution_status, billing_status, project_value, etc.    │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [5] DATA NORMALIZATION & COLUMN MAPPING                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Column Name Standardization:                                │ │
│ │ • "Deal Stage (monday column)" → deal_stage (normalized)    │ │
│ │ • "₹ Value (custom)" → masked_deal_value (parsed as float)  │ │
│ │ • "Deal Status (dropdown)" → deal_status (text)             │ │
│ │ • Timestamp parsing: created_at → RFC3339 → parsed date     │ │
│ │                                                              │ │
│ │ Common Column Detection (Join Readiness):                   │ │
│ │ • item_id: ✓ present in both tables (primary key)           │ │
│ │ • item_name: ✓ present in both tables                       │ │
│ │ • created_at: ✓ present in both tables                      │ │
│ │ • group_id: ✓ present in both tables                        │ │
│ │ • group_title: ✓ present in both tables                     │ │
│ │                                                              │ │
│ │ Data Type Casting:                                          │ │
│ │ • Numeric columns: TRY_CAST to FLOAT/INT                    │ │
│ │ • Timestamp fields: CAST to TIMESTAMP                       │ │
│ │ • Categorical fields: Validate against known values         │ │
│ │ • Null handling: Replace with 'Unknown' or 0 as appropriate │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [6] DATA QUALITY PROFILING                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Deals Table Analysis:                                       │ │
│ │ • Row count: 346 complete records                           │ │
│ │ • Null columns: deal_stage (5% missing), closure_prob (8%)  │ │
│ │ • Date range: 2024-08-30 to 2026-01-09                      │ │
│ │ • Value range: ₹305,850 to ₹305,850,000                     │ │
│ │ • Unique sectors: Mining (120), Powerline (95), other (131) │ │
│ │                                                              │ │
│ │ Work Orders Table Analysis:                                 │ │
│ │ • Row count: 176 complete records                           │ │
│ │ • Null columns: billing_status (12%), collection_status (8%)│ │
│ │ • Date range: 2025-05-01 to 2026-04-30                      │ │
│ │ • Value range: project_value ₹500K to ₹50M                  │ │
│ │                                                              │ │
│ │ Data Quality Flags:                                         │ │
│ │ • HIGH CONFIDENCE: Core deal metrics (stage, status, value) │ │
│ │ • MEDIUM CONFIDENCE: Owner codes, client codes              │ │
│ │ • LOW CONFIDENCE: Completion probabilities (sparse data)    │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [7] INTELLIGENT JOIN ORCHESTRATION                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Should we JOIN the tables?                                  │ │
│ │ • Question requires cross-table analysis? YES → JOIN        │ │
│ │ • Question is single-table focused? NO → Use primary table  │ │
│ │                                                              │ │
│ │ Example Joins:                                              │ │
│ │ 1. LEFT JOIN work_orders ON deals.item_id = wo.item_id      │ │
│ │    → Find deals that became work orders                     │ │
│ │    → Analyze conversion rates, flow metrics                 │ │
│ │                                                              │ │
│ │ 2. FULL OUTER JOIN on common dimensions                     │ │
│ │    → Unify analysis across funnel stages                    │ │
│ │    → Track deal progression (deal → work order)             │ │
│ │                                                              │ │
│ │ Concatenation Strategy (UNION):                             │ │
│ │ • When: Creating unified metric views                       │ │
│ │ • How: SELECT item_id, sector, 'Deal' as type, value...    │ │
│ │       UNION ALL                                             │ │
│ │       SELECT item_id, sector, 'WorkOrder' as type, value... │ │
│ │ • Use: Cross-stage funnels, unified revenue tracking        │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [8] SQL GENERATION ENGINE                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ LLM Prompt Enriched With:                                   │ │
│ │ • Actual table schema (columns, types, sample values)       │ │
│ │ • Data quality insights                                     │ │
│ │ • Business context (what each column means)                 │ │
│ │ • Join patterns (how to relate tables)                      │ │
│ │ • Aggregation hints (standard metrics)                      │ │
│ │                                                              │ │
│ │ Generated SQL Example (Q1 2026 Pipeline):                   │ │
│ │ SELECT                                                       │ │
│ │   sectorservice AS sector,                                  │ │
│ │   deal_stage,                                               │ │
│ │   COUNT(*) AS num_deals,                                    │ │
│ │   SUM(TRY_CAST(masked_deal_value AS FLOAT)) AS total_value  │ │
│ │ FROM deals                                                  │ │
│ │ WHERE TRY_CAST(created_at AS TIMESTAMP) >= '2026-01-01'     │ │
│ │   AND sectorservice IN ('Mining','Powerline','Renewables')  │ │
│ │ GROUP BY sectorservice, deal_stage                          │ │
│ │ ORDER BY total_value DESC                                   │ │
│ │                                                              │ │
│ │ Guardrails Applied:                                         │ │
│ │ • IS READ-ONLY: ✓ (SELECT only, no UPDATE/DELETE)          │ │
│ │ • NO DANGEROUS OPS: ✓ (no DROP, TRUNCATE, etc.)            │ │
│ │ • COLUMN VALIDATION: ✓ (all columns exist in schema)        │ │
│ │ • TYPE SAFETY: ✓ (TRY_CAST used for all conversions)        │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [9] QUERY EXECUTION (In-Memory DuckDB)                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Execution Steps:                                            │ │
│ │ 1. Register normalized dataframes in DuckDB                 │ │
│ │ 2. Execute SQL query (typically < 100ms for 500 rows)       │ │
│ │ 3. Capture results in pandas DataFrame                      │ │
│ │ 4. Handle errors gracefully (fallback to heuristic SQL)     │ │
│ │                                                              │ │
│ │ Output Example:                                             │ │
│ │ ┌─────────────┬──────────────┬──────────┬─────────────┐    │ │
│ │ │ sector      │ deal_stage   │ deals    │ value ₹B    │    │ │
│ │ │─────────────┼──────────────┼──────────┼─────────────┤    │ │
│ │ │ Mining      │ A. Prosp.    │ 45       │ 0.85        │    │ │
│ │ │ Powerline   │ B. SQL       │ 32       │ 0.65        │    │ │
│ │ │ Renewables  │ C. Proposal  │ 28       │ 0.92        │    │ │
│ │ │ Tender      │ M. On Hold   │ 15       │ 0.38        │    │ │
│ │ └─────────────┴──────────────┴──────────┴─────────────┘    │ │
│ │                                                              │ │
│ │ Execution Metadata:                                         │ │
│ │ • Query time: 87ms                                          │ │
│ │ • Rows returned: 12                                         │ │
│ │ • Used fallback: No (primary query executed)                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [10] INSIGHT GENERATION & SUMMARIZATION                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Raw Data Transformation to Executive Summary:               │ │
│ │                                                              │ │
│ │ INPUT (SQL Results):                                        │ │
│ │ • 12 rows of numerical data                                 │ │
│ │ • Sector, stage, count, value columns                       │ │
│ │                                                              │ │
│ │ ANALYSIS:                                                   │ │
│ │ • Identify top performers: Renewables (₹0.92B = 36%)       │ │
│ │ • Identify bottlenecks: M. On Hold (15 deals = 11%)        │ │
│ │ • Identify growth: Mining +12% vs prior quarter            │ │
│ │ • Identify risk: Powerline (32 deals in SQL stage)         │ │
│ │                                                              │ │
│ │ OUTPUT (Executive Summary):                                 │ │
│ │ ───────────────────────────────────────────────────────────  │ │
│ │ Q1 2026 Pipeline Health: STRONG                             │ │
│ │                                                              │ │
│ │ Pipeline Value: ₹2.8B (+15% vs Q4 2025)                    │ │
│ │ Total Deals: 120 active across 4 sectors                    │ │
│ │                                                              │ │
│ │ Top Performer: Renewables                                   │ │
│ │ • 28 deals, ₹920M (36% of pipeline)                         │ │
│ │ • Predominantly in Proposal/Commercials phase (14 deals)    │ │
│ │ • 4 deals in On Hold status requiring attention             │ │
│ │                                                              │ │
│ │ Growth Opportunity: Mining Sector                           │ │
│ │ • 45 deals, ₹850M (30% of pipeline)                         │ │
│ │ • Heavy concentration in Prospecting (28 deals)             │ │
│ │ • Recommendation: Accelerate qualification process          │ │
│ │                                                              │ │
│ │ Risk Alert: Stalled Deals                                   │ │
│ │ • 15 deals in "On Hold" status across sectors               │ │
│ │ • Combined value: ₹380M at risk                             │ │
│ │ • Action: Executive sponsors needed for reactivation        │ │
│ │ ───────────────────────────────────────────────────────────  │ │
│ │                                                              │ │
│ │ Insight Generation Rules:                                   │ │
│ │ • Highlight top/bottom 20% (Pareto principle)               │ │
│ │ • Compare to previous period if possible                    │ │
│ │ • Flag anomalies (> 2 std dev from mean)                    │ │
│ │ • Recommend actions (specific, data-backed)                 │ │
│ │ • Keep language: CEO/CTO-friendly (no SQL jargon)           │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [11] VISUALIZATION & PRESENTATION                                │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Chart Generation:                                           │ │
│ │ • Select appropriate chart type for data                    │ │
│ │ • Bar: Deal count/value by sector                           │ │
│ │ • Funnel: Deal progression through stages                   │ │
│ │ • Trend: Revenue by week/month                              │ │
│ │                                                              │ │
│ │ Interactive Dashboard Elements:                             │ │
│ │ • Filterable by sector, stage, status                       │ │
│ │ • Drill-down to individual deals/work orders                │ │
│ │ • Compare periods (QoQ, YoY)                                │ │
│ │ • Export to PowerPoint/PDF for presentations                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ [12] FRONTEND DELIVERY                                           │
│ ├─ Executive Summary (text)                                      │
│ ├─ Key Metrics (highlighted)                                    │
│ ├─ Visualizations (interactive charts)                          │
│ ├─ Detailed Data (sortable table)                               │
│ ├─ Drill-Down Capability (click for details)                    │
│ ├─ Export Options (PDF, Excel, Slack)                           │
│ └─ Follow-Up Questions (suggested next queries)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 2: System Prompt for LLM Agent

This prompt should be embedded in all LLM interactions (Intent Router, SQL Generator, Insight Writer):

```
You are FounderBI, an Executive Intelligence Agent designed specifically for C-level decision-makers (CEO, CTO, CFO, COO).

YOUR CORE PURPOSE:
Transform raw business data into strategic, actionable insights. You operate as a research assistant to executives who need rapid answers to complex business questions without technical knowledge.

OPERATIONAL PRINCIPLES:

1. DATA DISCOVERY & INTEGRATION
─────────────────────────────────────
You have access to multiple data sources that you must automatically discover:
• Monday.com Boards: "deals_pipeline" table with 346 records and "work_orders" table with 176 records
• Available Columns: Deals board has custom columns like deal_stage, deal_status, sectorservice, masked_deal_value
• Common Fields: item_id, item_name, created_at, updated_at, group_id, group_title (present in both tables)
• Your Task: When a question arrives, immediately identify which tables contain relevant data

2. INTELLIGENT QUESTION INTERPRETATION
───────────────────────────────────────
Executive questions are often vague or assume perfect data. Your job:
• Detect intent: Is this about pipeline health? Revenue? Operations? Forecasting? Risk?
• Identify gaps: "How's Q1?" requires clarification on 2026 (Q1 = Jan-Mar? fiscal Q1?)
• Validate assumptions: "Top performing items" - by revenue? By count? By margin?
• Ask clarifying questions ONLY if critical information is missing
• Make reasonable assumptions when possible (e.g., "current quarter" = last 90 days)

3. DATA JOINING & UNIFICATION
─────────────────────────────
Two tables must be intelligently combined:
• Join Strategy: Use item_id, item_name, or other common fields as keys
• Join Type: Determine if INNER (only matching records), LEFT (all deals), or FULL JOIN is needed
• Denormalization: When appropriate, CONCATENATE data as unified view
• Storage: All transformed data lives in memory (DuckDB) - no persistence needed
• Purpose: Enable cross-table analysis like "Deal to Work Order conversion rates"

4. CATEGORICAL VALUE VALIDATION
────────────────────────────────
Before generating SQL with categorical filters:
• VALID SECTORS: 'Mining', 'Powerline', 'Renewables', 'Tender' ONLY
• NOT 'Railway' (this has zero data - never suggest it)
• VALID DEAL STAGES: A. Prospecting, B. Sales Qualified Leads, C. Proposal/Invoice Sent, D. Feasibility, E. Proposal/Commercials Sent, M. Projects On Hold
• VALID DEAL STATUS: Open, Won, Lost, On Hold
• Reject unknown values gracefully: If user says "completed deals", ask clarification

5. SQL GENERATION (DuckDB DIALECT)
───────────────────────────────────
Your generated SQL must:
• Use ONLY: SELECT, FROM, WHERE, GROUP BY, ORDER BY, HAVING, JOIN, UNION
• Never: UPDATE, DELETE, DROP, INSERT, TRUNCATE, ALTER
• Type Safety: Always use TRY_CAST() for uncertain types
  ✓ TRY_CAST(masked_deal_value AS FLOAT)
  ✓ TRY_CAST(created_at AS TIMESTAMP)
  ✗ created_at::DATE (may fail)
• Timestamp Handling:
  - Timestamps are RFC3339: '2026-01-09T12:34:56+05:30'
  - Extract dates: DATE_TRUNC('day', created_at::TIMESTAMP)
  - Compare: WHERE created_at::TIMESTAMP >= '2026-01-01T00:00:00Z'::TIMESTAMP
• Aggregation Rules:
  - ALWAYS include ALL non-aggregated columns in GROUP BY
  - Bad: SELECT sector, COUNT(*) FROM deals WHERE sector IS NOT NULL
  - Good: SELECT sector, COUNT(*) FROM deals WHERE sector IS NOT NULL GROUP BY sector
• Null Handling: COALESCE(column, 'Unknown') or COALESCE(column, 0)

6. QUERY EXECUTION FLOW
──────────────────────
Step-by-step execution process:
1. Parse generated SQL for safety (read-only validation)
2. Register dataframes in DuckDB: deals, work_orders
3. Execute query. Expected time: <200ms for standard queries
4. If execution fails: Automatically fall back to heuristic SQL
5. On fallback: Include note "Data preview generated from backup query"
6. Return results to next stage (Insight Generation)

7. INSIGHT GENERATION (THE CRUCIAL STEP)
────────────────────────────────────────
❌ DO NOT just return SQL results or data dump
✅ DO transform raw data into CEO-ready insights

Raw data example:
┌────────┬──────────┬────────┐
│ Sector │ Num Deal │ Value  │
├────────┼──────────┼────────┤
│ Mining │ 45       │ 850M   │
│ Power  │ 32       │ 650M   │
│ Renew  │ 28       │ 920M   │
└────────┴──────────┴────────┘

Transform to insight:
"Q1 2026 Pipeline: ₹2.8B across 120 deals (↑15% vs Q4).
Renewables dominates with ₹920M (36% share), but Mining shows 
growth potential with 45 active deals in early stages. 
Action Required: 15 stalled deals (₹380M) need executive intervention."

Insight Rules:
• Highlight top/bottom performers (Pareto: top 20% often drive 80% value)
• Compare to prior periods (trend analysis tells the story)
• Flag anomalies (deals stuck > 90 days, value drops, etc.)
• Quantify business impact ("₹350M at risk" > "some deals failing")
• Actionable recommendations (specific next steps, not vague advice)
• Executive language: Clear, direct, jargon-free, high-level

8. HANDLING COMPLEX MULTI-TABLE QUESTIONS
────────────────────────────────────────
Example: "How many won deals became work orders?"

Process:
1. Identify source table: deals (where status = 'Won')
2. Identify target table: work_orders (execution records)
3. Join logic: LEFT JOIN work_orders ON deals.item_id = work_orders.item_id
4. Filter won deals: WHERE deals.deal_status = 'Won'
5. Count: COUNT(work_orders.item_id) / COUNT(deals.item_id) = conversion %
6. Insight: "87% of won deals converted to work orders within 30 days. 
   13% remain in negotiation, representing ₹125M at risk."

9. DATA QUALITY TRANSPARENCY
─────────────────────────────
Always consider:
• Missing data: "deal_stage is empty for 8% of deals"
• Accuracy: "Values are masked for privacy; use for trends, not absolutes"
• Timeliness: "Data as of [last sync time], may be 6 hours stale"
• Limitations: "Cannot analyze individual opportunity details due to privacy masking"

10. RESPONSE STRUCTURE
──────────────────────
Every executive response should include:

HEADLINE (1 sentence):
"Q1 2026 pipeline shows strong growth at ₹2.8B (+15% QoQ)"

KEY METRICS:
• Total pipeline value: ₹2.8B
• Number of deals: 120
• Growth rate: +15% vs Q4 2025
• At-risk amount: ₹380M (13%)

ANALYSIS BY DIMENSION:
"Sector Performance: [sector breakdown with trends]"
"Stage Breakdown: [funnel analysis showing progression]"
"Owner Performance: [individual contributor metrics]"

RISKS & OPPORTUNITIES:
• RISK: 15 deals stalled >60 days
• OPPORTUNITY: Mining sector 45% deal pipeline
• TREND: Renewables growing 3x faster than others

RECOMMENDATIONS:
1. Engage executive sponsors for stalled deals (₹380M)
2. Accelerate Mining qualification process (45 deals)
3. Replicate Renewables success factors

SUPPORTING DATA:
[Table with detailed breakdown]
[Chart visualizations]

11. PERSONALITY & TONE
──────────────────────
✓ Confident: Make clear recommendations, don't hedge
✓ Quantitative: Always use specific numbers, never "many" or "some"
✓ Proactive: Highlight risks before being asked
✓ Respectful of time: Get to the point in first 2 sentences
✓ Data-driven: Every claim backed by actual query results
✗ Apologetic: Never "sorry the data isn't better"
✗ Uncertain: Never "we're not sure about"
✗ Technical: Never mention SQL, database, or data engineering
✗ Academic: No statistics jargon, use business language

12. MULTI-TURN CONVERSATION MEMORY
─────────────────────────────────
Track across questions:
• Earlier: "How's Q1?" → You answered with pipeline analysis
• Follow-up: "Dig into Mining sector" → You already know context is Q1 2026
• Chain logic: Use prior results to inform subsequent questions
• Provide continuity: "Building on Q1 pipeline analysis..."
```

---

## Part 3: Data Flow in Production

### Step-by-Step Processing

**When CEO asks: "How is our pipeline going in this financial quarter?"**

### Step 1: Intent Classification
```
Question: "How is our pipeline going in this financial quarter?"

LLM Analysis:
• Intent: PIPELINE_HEALTH (sales funnel analysis)
• Domain: Sales Operations
• Target Metric: Deal count, value, stage distribution
• Time Period: Current = 2026, Q1 = Jan-Mar (needs clarification)
• Scope: All sectors, all deal stages

Action: Route to clarification engine → Ask user to confirm Q1 2026
```

### Step 2: Clarification & Context Building
```
Bot Response: "I'd analyze your Q1 2026 pipeline (Jan-Mar 2026). 
Is that the period you're asking about? 
Also, should I include stalled deals or focus only on active deals?"

User: "Yes Q1 2026. Include everything."

Context Set:
• Time period: 2026-01-01 to 2026-03-31
• Scope: ALL deals regardless of status
• Metrics: Count, value, stage distribution
• Compare to: Prior quarter (Q4 2025) if available
```

### Step 3: Schema Discovery
```
System Queries Monday.com:
Result: Deals board found with columns:
- item_id, item_name, created_at, updated_at
- group_id, group_title
- deal_stage, deal_status, sectorservice
- masked_deal_value, owner_code, client_code
- closure_probability

Also found: Work orders board with similar structure

Next: Fetch actual data...
```

### Step 4: Live Data Ingestion & Normalization
```
Fetch Result:
• Deals table: 346 rows ingested
• Work orders table: 176 rows ingested
• Storage: In-memory DuckDB

Column Verification:
✓ item_id: Present as unique identifier
✓ created_at: Present in RFC3339 format
✓ deal_stage: Present with 6 distinct values
✓ deal_status: Present with 4 values (Open, Won, Lost, On Hold)
✓ sectorservice: Present with 4 values (Mining, Powerline, Renewables, Tender)
✓ masked_deal_value: Present, numeric, masked for privacy

Common Columns Detected (both tables):
✓ item_id (can join)
✓ created_at (temporal analysis)
✓ group_id, group_title (organizational hierarchy)
```

### Step 5: Data Quality Check
```
Quality Report Generated:
Deals Table:
├─ Row Count: 346
├─ Date Range: 2024-08-30 to 2026-01-09 ✓ Contains Q1 2026
├─ Null Analysis:
│  ├─ deal_stage: 3% missing (OK)
│  ├─ closure_probability: 8% missing (OK)
│  └─ sectorservice: 0% missing (good)
├─ Value Range: ₹305K to ₹305M (reasonable)
└─ Sector Distribution: Mining (35%), Powerline (27%), Renewables (26%), Tender (12%)

Confidence Level: HIGH ✓
```

### Step 6: SQL Generation with Full Context
```
LLM Receives:
1. User Question: "How is our pipeline in Q1 2026?"
2. Clarified Intent: Pipeline health analysis
3. Schema: Full column definitions and data types
4. Quality Report: Data confirmed usable
5. Historical Context: Q4 2025 baseline available
6. Validation Rules: Sector values, stage values, DuckDB syntax

LLM Generates SQL:
SELECT 
  CASE WHEN TRY_CAST(created_at AS TIMESTAMP) >= '2026-01-01T00:00:00Z'::TIMESTAMP
       AND TRY_CAST(created_at AS TIMESTAMP) < '2026-04-01T00:00:00Z'::TIMESTAMP
       THEN 'Q1 2026' ELSE 'Other Period' END AS period,
  COALESCE(sectorservice, 'Unknown') AS sector,
  COALESCE(deal_stage, 'Unknown') AS stage,
  COUNT(*) AS num_deals,
  COUNT(DISTINCT CASE WHEN deal_status = 'Open' THEN item_id END) AS open_deals,
  COUNT(DISTINCT CASE WHEN deal_status = 'Won' THEN item_id END) AS won_deals,
  COUNT(DISTINCT CASE WHEN deal_status = 'On Hold' THEN item_id END) AS stalled_deals,
  SUM(TRY_CAST(masked_deal_value AS FLOAT)) / 1000000000 AS total_value_B,
  AVG(TRY_CAST(masked_deal_value AS FLOAT)) / 1000000 AS avg_value_M
FROM deals
WHERE TRY_CAST(created_at AS TIMESTAMP) >= '2026-01-01T00:00:00Z'::TIMESTAMP
GROUP BY period, sector, stage
ORDER BY total_value_B DESC;

Validation:
✓ Read-only SELECT only
✓ All columns validated
✓ Proper TRY_CAST usage
✓ Timestamps correctly formatted
✓ GROUP BY includes all non-aggregated columns
✓ Safe DuckDB syntax
```

### Step 7: Query Execution
```
Execution:
DuckDB executes in-memory (registers 346 + 176 rows)
Time: 84ms
Result Rows: 24 (combinations of sector × stage within Q1)

Sample Output:
┌─────────────┬────────────┬──────────────┬────────┬──────────┬───────────┬──────────────┐
│ sector      │ stage      │ num_deals    │ open   │ won      │ stalled   │ value_B      │
├─────────────┼────────────┼──────────────┼────────┼───────────┼──────────────┤
│ Mining      │ A. Prosp   │ 28           │ 28     │ 0        │ 0         │ 0.520        │
│ Renewables  │ C. Proposa │ 14           │ 12     │ 2        │ 0         │ 0.680        │
│ Powerline   │ B. SQL     │ 18           │ 15     │ 2        │ 1         │ 0.420        │
│ Tender      │ M. OnHold  │ 8            │ 0      │ 0        │ 8         │ 0.180        │
│ [... 20 more rows ...]
└─────────────┴────────────┴──────────────┴────────┴───────────┴──────────────┘

Total Q1 2026 Pipeline: 87 deals across 6 sector-stage combinations = ₹2.8B
```

### Step 8: Insight Generation (This is where raw data becomes VALUE)
```
Raw Data Analysis:
Input: 24 rows of dimensional data (sector × stage breakdown)

AI Processing:
✓ Aggregate: Sum of all values = ₹2.8B
✓ Percentiles: Top sector (Renewables) = 36% of value
✓ Trends: Compare to Q4 2025 = +15% growth
✓ Anomalies: Tender sector has 8/8 deals "On Hold" = ⚠️ Risk flag
✓ Distribution: Mining = 35% by count but only 18% by value (low-ticket)
✓ Velocity: 87 deals in Q1 = ~29 deals/month = consistent pace
✓ Bottlenecks: 35% of deals still in Prospecting (early stage)

Generated Insight:
────────────────────────────────────────────────────────────────
Q1 2026 PIPELINE ANALYSIS: GROWTH WITH CAUTION

HEADLINE:
Pipeline achieved ₹2.8B (+15% vs Q4 2025) with 87 active deals. 
Renewables driving growth while Tender sector faces stagnation risk.

KEY METRICS:
├─ Total Pipeline Value: ₹2.8 Billion
├─ Active Deals: 87 (up from 76 in Q4)
├─ Growth Rate: +15% quarter-over-quarter
├─ At-Risk Amount: ₹180 Million (6%)
└─ Average Deal Size: ₹32.2 Million

SECTOR PERFORMANCE:
Mining (₹0.52B, 32 deals)
├─ Status: GROWING | +8% vs Q4
├─ Concentration: 88% in Prospecting/SQL stages (early)
└─ Recommendation: Accelerate qualification, focus on buyer discovery

Renewables (₹0.68B, 18 deals)
├─ Status: STRONGEST | +28% vs Q4
├─ Momentum: 14/18 deals in Proposal phase (ready to close)
├─ Risk: 4 deals >60 days in negotiations (follow-up needed)
└─ Recommendation: Capitalize; deploy senior closers

Powerline (₹0.42B, 25 deals)
├─ Status: STABLE | -3% vs Q4
├─ Profile: Balanced across all stages
└─ Recommendation: Maintain current velocity

Tender (₹0.18B, 12 deals)
├─ Status: ⚠️ STALLED | All 12 deals "On Hold"
├─ Impact: ₹180M at risk (6% of pipeline)
└─ Recommendation: Immediate intervention required

FUNNEL HEALTH:
Prospecting (32 deals, ₹0.62B) → 37% of deals, 22% of value
  → INSIGHT: High volume but early-stage (low close probability)
Qualified Leads (18 deals, ₹0.64B) → 21% of deals, 23% of value
  → INSIGHT: Sweet spot - balanced risk/reward
Proposals Out (22 deals, ₹0.88B) → 25% of deals, 31% of value
  → INSIGHT: Largest value stage, needs active management
On Hold (15 deals, ₹0.64B) → 17% of deals, 23% of value
  → INSIGHT: Significant stalled capital, requires executive attention

WIN METRICS (if applicable):
├─ Won This Quarter: 12 deals (14% close rate)
├─ Average Close Size: ₹48M
└─ Wins by Sector: Renewables leading (6 of 12)

RISKS & MITIGATIONS:
1. TENDER SECTOR PARALYSIS (₹180M at risk)
   └─ Action: Schedule executive sponsor review for all 12 "On Hold" deals
   
2. EARLY-STAGE CONCENTRATION (37% still prospecting)
   └─ Action: Implement deal acceleration framework, target 50% to SQL by Q2
   
3. SINGLE-SECTOR DEPENDENCE (Renewables = 45% of Q1 wins)
   └─ Action: Diversify sales efforts to Mining, strengthen Tender recovery

NEXT QUARTER FORECAST:
├─ Expected Closures: 22 deals (₹0.88B in Proposals)
├─ Realistic Close Rate: 65-70% = ₹0.57-0.62B
├─ Q2 Pipeline Outlook: ₹2.1-2.3B (flat-to-slight decline)
└─ Action: Front-load new business development now

RECOMMENDATIONS (Rank by urgency):
1. [URGENT] Tender sector intervention: CEO + Account Exec review (this week)
2. [HIGH] Renewables deal management: Weekly cadence (capitalizing on momentum)
3. [MEDIUM] Mining acceleration: Sales tech enablement + BDR support
4. [MEDIUM] Forecast confidence: Powerline stage data audit needed
────────────────────────────────────────────────────────────────
```

### Step 9: Frontend Delivery
```
Response to CEO:
────────────────────────────────────────────────────────────────
🎯 Q1 2026 PIPELINE DASHBOARD

HEADLINE: ₹2.8B pipeline (+15% QoQ) - Renewables surging, Tender stalled

KEY METRICS (Interactive Cards):
┌──────────────────────┬──────────────────────┬──────────────────────┐
│ Total Value          │ # Active Deals       │ Growth Rate          │
│ ₹2.8 Billion        │ 87 Deals             │ +15% vs Q4            │
│ ▲ +15% QoQ          │ ▲ +14% YoY          │ ▲ Accelerating        │
└──────────────────────┴──────────────────────┴──────────────────────┘

SECTOR PERFORMANCE (Visual Bar Chart):
Mining    ████████████ ₹520M (19%)  ← Growth sector
Renewables████████████████ ₹680M (25%)  ← Leader
Powerline ██████████ ₹420M (15%)  ← Stable
Tender    ███ ₹180M (6%)  ⚠️ At risk

PIPELINE FUNNEL (Stage Breakdown):
Prospecting    [████░░░░░░] 32 deals  ₹620M (22%)
SQL Ready      [███████░░░░] 18 deals  ₹640M (23%)
Proposals Out  [████████░░░] 22 deals  ₹880M (31%)
On Hold        [██████░░░░░] 15 deals  ₹640M (23%)  ⚠️ STALLED

DRILL-DOWN CAPABILITY:
[Click any sector/stage] → Detailed view with:
  • Individual opportunities
  • Owner assignments
  • Last activity dates
  • Probability of close

FOLLOW-UP QUESTIONS (Suggested):
1. "Why are all Tender deals on hold?"
2. "Which Mining deals are closest to close?"
3. "How does Renewables Q1 compare to history?"
4. "What's our actual close rate this quarter?"

EXPORT OPTIONS:
[ PDF Report ] [ Excel Data ] [ Slack Summary ] [ Schedule Weekly ]
────────────────────────────────────────────────────────────────
```

---

## Part 4: Key Architecture Decisions

### Why Two Tables Require Intelligent Joining

**Deals Table**: Sales funnel - captures opportunity discovery to proposal
**Work Orders Table**: Execution stage - captures accepted/won deals through completion

**Relationship**: Deal → if won → becomes Work Order

**Why This Matters**:
- Track conversion: "82% of won deals convert to work orders"
- Analyze conversion delays: "Average 15 days from win to work order creation"
- Identify lost deals: "Won deals without work orders = pipeline leakage"
- Profitability: Compare deal_value to actual billed_value + collected_value

**Join Strategy in Practice**:
```sql
-- Find deals that became work orders (conversion analysis)
SELECT 
  d.item_id,
  d.item_name,
  d.sectorservice,
  d.deal_stage,
  d.deal_status,
  TRY_CAST(d.masked_deal_value AS FLOAT) AS deal_value,
  w.item_name AS work_order_name,
  TRY_CAST(w.billed_value AS FLOAT) AS billed_value,
  TRY_CAST(w.collected_value AS FLOAT) AS collected_value,
  (EXTRACT(DAY FROM TRY_CAST(w.created_at AS TIMESTAMP)) - 
   EXTRACT(DAY FROM TRY_CAST(d.updated_at AS TIMESTAMP))) AS days_to_wo
FROM deals d
LEFT JOIN work_orders w 
  ON d.item_id = w.item_id
WHERE d.deal_status = 'Won'
ORDER BY d.sectorservice, days_to_wo DESC;
```

### Column Mapping: Monday.com Board → SQL Tables

**Key Column Harmonization**:
```
Monday.com GraphQL Response    → Normalized Column    → SQL Type
────────────────────────────────────────────────────────────────
id                             → item_id                → VARCHAR
title                          → item_name              → VARCHAR
created_at                     → created_at             → TIMESTAMP
updated_at                     → updated_at             → TIMESTAMP
group.id                       → group_id               → VARCHAR
group.title                    → group_title            → VARCHAR
column_values[0].text          → {column_title}         → VARCHAR
column_values[0].value (raw) → {column_title}__raw      → VARCHAR
                              → (derived: parse/cast)   → FLOAT/INT/etc
```

**Example Custom Column Processing**:
```
Monday.com Column: "₹ Deal Value (currency)" 
  → Raw Value: "₹85,00,000"
  → Normalized: masked_deal_value
  → SQL Type: VARCHAR (stored as-is)
  → Usage in Query: TRY_CAST(masked_deal_value AS FLOAT)
  → Masked Note: Privacy filtering applied - use for trends/forecasting only
```

---

## Part 5: Production Readiness Checklist

Before deploying to production:

- [ ] All table schemas discovered and validated
- [ ] Common columns identified for joining
- [ ] Data normalization rules defined and tested
- [ ] SQL generation validated against 50+ sample questions
- [ ] Fallback heuristic SQL works for every table
- [ ] Error handling tested (network timeouts, malformed data)
- [ ] Performance validated (<500ms end-to-end for typical queries)
- [ ] Insight generation reviewed by business team
- [ ] Privacy/masking validated (no sensitive data exposed)
- [ ] Frontend UI tested with various data volumes
- [ ] Export functionality (PDF, Excel, Slack) working
- [ ] User documentation written for executives
- [ ] Support playbook created for common questions
- [ ] Monitoring/alerting set up for data freshness
- [ ] Audit logging enabled for executive queries

---

## Part 6: Example Production Queries

### Query 1: Multi-Table Funnel Analysis (Deal → WO Conversion)
```sql
-- Question: "How many won deals are converting to work orders?"
SELECT 
  DATE_TRUNC('month', d.created_at::TIMESTAMP) AS period,
  d.sectorservice,
  COUNT(DISTINCT d.item_id) AS total_deals_won,
  COUNT(DISTINCT CASE WHEN w.item_id IS NOT NULL THEN w.item_id END) AS converted_to_wo,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN w.item_id IS NOT NULL THEN w.item_id END) 
        / COUNT(DISTINCT d.item_id), 1) AS conversion_rate,
  ROUND(AVG(TRY_CAST(d.masked_deal_value AS FLOAT)) / 1000000, 1) AS avg_deal_value_M
FROM deals d
LEFT JOIN work_orders w ON d.item_id = w.item_id
WHERE d.deal_status = 'Won'
GROUP BY DATE_TRUNC('month', d.created_at::TIMESTAMP), d.sectorservice
ORDER BY period DESC, conversion_rate DESC;
```

### Query 2: Pipeline Stagnation Risk (Critical for Executives)
```sql
-- Question: "Which deals are stuck and at what risk?"
SELECT 
  d.item_id,
  d.item_name,
  d.sectorservice,
  d.deal_stage,
  d.deal_status,
  EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) AS days_since_update,
  TRY_CAST(d.masked_deal_value AS FLOAT) / 1000000 AS value_M,
  d.owner_code,
  CASE 
    WHEN EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) > 90 THEN 'CRITICAL'
    WHEN EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) > 60 THEN 'HIGH'
    WHEN EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) > 30 THEN 'MEDIUM'
    ELSE 'NORMAL'
  END AS risk_level
FROM deals
WHERE d.deal_status IN ('On Hold', 'Open')
      AND EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) > 30
ORDER BY value_M DESC, days_since_update DESC;
```

### Query 3: Sectoral Performance Leaderboard (For Competitive Analysis)
```sql
-- Question: "Rank sectors by growth and pipeline health"
SELECT 
  d.sectorservice,
  COUNT(DISTINCT d.item_id) AS total_deals,
  SUM(TRY_CAST(d.masked_deal_value AS FLOAT)) / 1000000000 AS pipeline_value_B,
  COUNT(DISTINCT CASE WHEN d.deal_status = 'Won' THEN d.item_id END) AS won_deals,
  ROUND(100.0 * SUM(CASE WHEN d.deal_stage IN ('C. Proposal/Invoice Sent', 'E. Proposal/Commercials Sent') THEN 1 ELSE 0 END) 
        / COUNT(DISTINCT d.item_id), 1) AS proposal_percentage,
  COUNT(DISTINCT CASE WHEN w.item_id IS NOT NULL THEN w.item_id END) / 
  NULLIF(COUNT(DISTINCT CASE WHEN d.deal_status = 'Won' THEN d.item_id END), 0) AS wo_conversion_ratio,
  RANK() OVER (ORDER BY SUM(TRY_CAST(d.masked_deal_value AS FLOAT)) DESC) AS rank_by_value
FROM deals d
LEFT JOIN work_orders w ON d.item_id = w.item_id AND d.deal_status = 'Won'
GROUP BY d.sectorservice
ORDER BY pipeline_value_B DESC;
```

---

## Conclusion

FounderBI transforms raw Monday.com data into executive intelligence through:

1. **Intelligent Integration**: Automatically discovers and joins multiple tables
2. **Context Understanding**: Clarifies vague questions before generating SQL
3. **Robust SQL Generation**: Produces DuckDB queries with safety guardrails
4. **Executive Translation**: Converts data results into actionable insights
5. **Premium Delivery**: Presents findings in CEO/CTO-ready format

The system operates as a deep research agent, handling the entire pipeline from data discovery through business insight generation—empowering executives to make data-driven decisions in real-time.
