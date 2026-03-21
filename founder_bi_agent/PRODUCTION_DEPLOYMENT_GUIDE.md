# FounderBI Agent - Complete Production Setup Instructions

## Overview

This document consolidates all production-level system instructions for the FounderBI agent—a deep research intelligence system serving executive decision-makers (CEO, CTO, CFO).

---

## Quick Start: What This System Does

**INPUT**: CEO asks → "How is our pipeline going in Q1?"

**SYSTEM FLOW**:
1. **Discover Intent** → Classify as PIPELINE_HEALTH analysis
2. **Clarify Context** → Confirm period (Q1 2026) and scope  
3. **Fetch Data** → Pull deals + work orders from Monday.com
4. **Normalize** → Column harmonization, data type casting
5. **Generate SQL** → LLM creates DuckDB query with schema context
6. **Execute** → Run query against in-memory dataset (346 + 176 rows)
7. **Transform** → Convert raw results into executive insight
8. **Deliver** → Return summary, metrics, charts, recommendations

**OUTPUT**: Executive summary with key metrics, analysis, risks, and next actions

---

## Production Configuration Checklist

### Data Pipeline Setup

- [ ] **Data Sources Configured**
  - Monday.com board names set: `MONDAY_DEALS_BOARD_NAME`, `MONDAY_WORK_ORDERS_BOARD_NAME`
  - API credentials configured: `MONDAY_API_TOKEN` or `MONDAY_MCP_SERVER_URL`
  - Data refresh strategy defined (on-demand vs scheduled)

- [ ] **Column Mapping Validated**
  - Core fields confirmed: item_id, item_name, created_at, updated_at  
  - Custom columns discovered: deal_stage, sectorservice, deal_status, etc.
  - Data types verified (strings, floats, timestamps)
  - Mask strategy confirmed (deal_value, sensitive info)

- [ ] **Data Quality Baseline**
  - Null/missing data patterns documented
  - Historical data range confirmed
  - Timezone handling verified (RFC3339 timestamps)
  - Unique value counts established for categorical columns

- [ ] **Join Strategy Defined**
  - Common columns identified: item_id, item_name, created_at
  - Join types determined: INNER, LEFT, FULL as needed
  - Cross-table analysis requirements mapped
  - Denormalization rules established

### LLM Configuration

- [ ] **Foundation LLM Set**
  - Primary model: Groq (llama-3.3-70b or qwen-2.5-coder recommended)
  - Fallback models: Gemini / Qwen / GLM
  - Temperature: 0.0 for SQL generation, 0.1 for insights
  - Max tokens: 4000+ for comprehensive insights

- [ ] **SQL Generation Model Set**
  - Primary: qwen-2.5-coder-32b (best for structured SQL)
  - Fallback: llama-3.3-70b-versatile
  - System prompt: Uses `SYSTEM_PROMPT_SQL_GENERATION`
  - Validation: Reads schemas + metadata context

- [ ] **Insight Generation Model Set**
  - Primary: llama-3.3-70b (best for narrative)
  - System prompt: Uses `SYSTEM_PROMPT_INSIGHT_GENERATION`  
  - Output format: Verified to match template (HEADLINE, METRICS, etc.)

- [ ] **Intent Classification Tested**
  - Model correctly routes: PIPELINE_HEALTH → Sales analysis
  - Model correctly routes: REVENUE_PERFORMANCE → Finance analysis
  - Model correctly routes: EXECUTION_HEALTH → Operations analysis
  - Fallback behavior tested (defaults to general_bi if unsure)

### Safety & Guardrails

- [ ] **SQL Validation Rules**
  - Read-only validation: SELECT only, no UPDATE/DELETE/DROP
  - Column existence check: All query columns exist in schema  
  - Type safety: ALL conversions use TRY_CAST()
  - Aggregation enforcement: GROUP BY includes all non-aggregated columns

- [ ] **Data Privacy**
  - Deal values are masked (numerical only, no 1:1 mapping)
  - Sensitive columns filtered before display
  - Null values handled gracefully (not exposed as blanks)
  - Individual-level data aggregated (no drill-to-person unless authorized)

- [ ] **Error Handling**
  - Fallback SQL tested for 10+ question types
  - Error messages don't expose technical details  
  - Rate limiting configured for API calls
  - Timeout configured: 30s for SQL execution

### Frontend Integration

- [ ] **API Endpoints Configured**
  - `POST /query` accepts question + conversation history
  - Response includes: answer, sql_query, result_records, chart_spec, quality_report
  - Error responses clear and actionable for user

- [ ] **UI Components Ready**
  - Executive summary display (text)
  - Key metrics cards (highlighted numbers)
  - Data table (sortable, filterable)
  - Chart visualization (auto-selected type)
  - Drill-down capability (click for details)
  - Export options (PDF, Excel, Slack)

- [ ] **Performance Optimized**
  - Queries execute in <500ms typical
  - Frontend displays results in <1s
  - Caching implemented for common queries
  - Pagination for large result sets (>1000 rows)

---

## File Structure & Locations

```
founder_bi_agent/
├── backend/
│   ├── llm/
│   │   ├── sql_prompt_context.py .......... SQL generation prompt + metadata
│   │   ├── foundation_prompts.py ......... Insight, intent, clarification prompts
│   │   ├── groq_client.py ............... LLM client (using new prompts)
│   │   ├── test_sql_prompt_enhancements.py .. Validation test suite
│   │   └── [other LLM providers]
│   ├── sql/
│   │   ├── sql_planner.py ............... SQL generation + heuristic fallback
│   │   ├── sql_guardrails.py ............ Read-only validation
│   │   ├── duckdb_engine.py ............ Query execution
│   │   ├── SQL_GENERATION_GUIDE.md ...... Debugging guide
│   │   └── ...
│   ├── graph/
│   │   ├── nodes.py .................... Workflow steps (main orchestration)
│   │   ├── state.py .................... State schema
│   │   └── workflow.py ................. DAG definition
│   ├── mcp/
│   │   └── monday_live.py .............. Monday.com API client
│   └── tools/
│       └── monday_bi_tools.py ........... Data fetching utilities
├── frontend/
│   ├── src/
│   │   ├── App.tsx .................... Main app
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx ....... Question input + response display
│   │   │   ├── ReasoningTrace.tsx ...... System trace visualization
│   │   │   ├── ThreeDScene.tsx ........ 3D visualization (optional)
│   │   │   └── TopBar.tsx ............. Header with metadata
│   │   └── services/
│   │       └── ai.ts ................. API client to backend
│   ├── index.html ..................... Entry point
│   └── vite.config.ts ................ Build config
├── scripts/
│   ├── export_bi_snapshot.py ......... Data export utility
│   ├── manual_pipeline_debug.py ...... Debugging helper
│   └── smoke_test_monday_bi_tools.py .. Smoke test
├── BI_AGENT_COMPLETE_FIX_GUIDE.md ... Implementation troubleshooting
├── PRODUCTION_WORKFLOW_GUIDE.md ..... This file (complete workflow)
└── SQL_GENERATION_IMPROVEMENTS_SUMMARY.md .. Prior session summary
```

---

## System Prompts Used in Production

### 1. SQL Generation (`SYSTEM_PROMPT_SQL_GENERATION`)
**Location**: `founder_bi_agent/backend/llm/sql_prompt_context.py`

**Purpose**: Teach LLM to generate valid DuckDB SQL queries

**Key Rules**:
- Use `created_at` (TIMESTAMP RFC3339), not `created_date`  
- Use `TRY_CAST()` for type conversions, not `::`
- Valid sectors only: Mining, Powerline, Renewables, Tender (NOT Railway)
- Always GROUP BY all non-aggregated columns
- Include examples of both ✅ correct and ❌ wrong SQL

### 2. Insight Generation (`SYSTEM_PROMPT_INSIGHT_GENERATION`)
**Location**: `founder_bi_agent/backend/llm/foundation_prompts.py`

**Purpose**: Transform raw data into CEO-ready insights

**Key Principles**:
- INSIGHT > DATA (explain what it means, not just facts)
- Top/bottom performers highlighted (Pareto analysis)
- Quantitative language (₹s, %, days, ranks)
- Risk-flagged proactively
- Actionable recommendations (specific next steps)
- Executive tone (confident, direct, no hedging)

### 3. Intent Classification (`SYSTEM_PROMPT_INTENT_CLASSIFICATION`)
**Location**: `founder_bi_agent/backend/llm/foundation_prompts.py`

**Purpose**: Route questions to correct analysis domain

**Supported Intents**:
- PIPELINE_HEALTH: Deal funnel, stages, velocity
- REVENUE_PERFORMANCE: Closed deals, closed value
- EXECUTION_HEALTH: Work order progression, billing
- CONVERSION_ANALYSIS: Deal-to-WO conversion, bottlenecks
- TEAM_PERFORMANCE: Individual contributor metrics
- SECTOR_ANALYSIS: Sector-specific performance
- BOTTLENECK_DISCOVERY: Where deals get stuck
- RISK_ASSESSMENT: At-risk deals, stalled deals
- FORECASTING: Q-o-Q, quarterly revenue outlook

### 4. Clarification (`SYSTEM_PROMPT_CLARIFICATION_EXPERT`)
**Location**: `founder_bi_agent/backend/llm/foundation_prompts.py`

**Purpose**: Ask minimum required clarifying questions

**Philosophy**: Make reasonable assumptions whenever possible; only ask critical questions

**Examples**:
- ✓ ASK: "Q1 2026 or fiscal Q1?" (changes the period)
- ✗ DON'T: "Do you want trend analysis?" (always include if possible)

---

## Example Production Queries (Reference)

### Query 1: Q1 2026 Pipeline Health
```sql
SELECT 
  COALESCE(sectorservice, 'Unknown') AS sector,
  COALESCE(deal_stage, 'Unknown') AS stage,
  COUNT(*) AS num_deals,
  SUM(TRY_CAST(masked_deal_value AS FLOAT)) / 1000000000 AS value_B,
  COUNT(CASE WHEN deal_status = 'Won' THEN 1 END) AS closed_count,
  ROUND(100.0 * COUNT(CASE WHEN deal_status = 'Won' THEN 1 END) / COUNT(*), 1) AS close_rate_pct
FROM deals
WHERE TRY_CAST(created_at AS TIMESTAMP) >= '2026-01-01T00:00:00Z'::TIMESTAMP
  AND TRY_CAST(created_at AS TIMESTAMP) < '2026-04-01T00:00:00Z'::TIMESTAMP
GROUP BY sectorservice, deal_stage
ORDER BY value_B DESC;
```

### Query 2: Deal-to-Work-Order Conversion
```sql
SELECT 
  d.sectorservice,
  COUNT(DISTINCT d.item_id) AS won_deals,
  COUNT(DISTINCT CASE WHEN w.item_id IS NOT NULL THEN w.item_id END) AS converted_to_wo,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN w.item_id IS NOT NULL THEN w.item_id END) 
        / NULLIF(COUNT(DISTINCT d.item_id), 0), 1) AS conversion_rate_pct,
  ROUND(AVG(EXTRACT(DAY FROM w.created_at::TIMESTAMP - d.updated_at::TIMESTAMP)), 0) AS avg_days_to_wo
FROM deals d
LEFT JOIN work_orders w ON d.item_id = w.item_id
WHERE d.deal_status = 'Won'
GROUP BY d.sectorservice
ORDER BY conversion_rate_pct DESC;
```

### Query 3: Risk Assessment (Stalled Deals)
```sql
SELECT 
  d.item_id,
  d.item_name,
  d.sectorservice,
  d.deal_stage,
  EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) AS days_stalled,
  TRY_CAST(d.masked_deal_value AS FLOAT) / 1000000 AS value_M,
  CASE 
    WHEN EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) > 90 THEN 'CRITICAL'
    WHEN EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) > 60 THEN 'HIGH'
    WHEN EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) > 30 THEN 'MEDIUM'
    ELSE 'OK'
  END AS risk_level
FROM deals
WHERE d.deal_status IN ('On Hold', 'Open')
  AND EXTRACT(DAY FROM NOW() - d.updated_at::TIMESTAMP) > 30
ORDER BY value_M DESC, days_stalled DESC;
```

---

## Deployment Verification Checklist

Before going live:

- [ ] Test 20 sample executive questions (e.g., "Pipeline health Q1?", "Top sectors?", "Revenue forecast?")
- [ ] Each question produces: valid SQL, executes without error, returns meaningful insight
- [ ] Verify SQL validation catches malicious queries (UPDATE, DELETE, DROP)
- [ ] Confirm fallback heuristic SQL works if primary LLM fails
- [ ] Verify timestamps parsed correctly as RFC3339 format
- [ ] Confirm null values handled gracefully throughout pipeline
- [ ] Test with various data volumes (100 rows, 500 rows, 5000 rows)
- [ ] Verify performance: <500ms for most queries, <2s for complex joins
- [ ] Confirm frontend displays insights without exposing raw SQL
- [ ] Test export functionality (PDF, Excel, Slack)
- [ ] Verify error messages are user-friendly
- [ ] Audit logs confirm all queries are read-only
- [ ] Security review: no sensitive data leakage
- [ ] Performance baseline: average query time documented

---

## Maintenance & Monitoring

### Weekly Monitoring

- [ ] Check data freshness: Last Monday.com sync timestamp
- [ ] Monitor error rates: Any SQL execution failures?
- [ ] Audit common questions: Are they being classified correctly?
- [ ] Performance check: Average query response time
- [ ] Quality check: Are insights generating correctly?

### Monthly Review

- [ ] Feedback from executives: Are insights accurate? Actionable?
- [ ] LLM model performance: Are prompts working? Need updates?
- [ ] Data quality: Any new null patterns? Changed column definitions?
- [ ] New business questions: Any patterns suggesting new analysis types?
- [ ] Cost analysis: LLM API spend, data transfer costs

### Quarterly Planning

- [ ] Capability expansion: New analysis types? New data sources?
- [ ] Performance optimization: Cache more queries? Improve model selection?
- [ ] Executive feedback incorporation: What worked? What didn't?
- [ ] Competitive analysis: Are we providing competitive intelligence?
- [ ] Strategic alignment: Are insights aligned with company goals?

---

## Troubleshooting Guide

### Issue: "Unknown column: created_date"
**Cause**: Prompt still assumes old column name
**Fix**: Verify `sql_prompt_context.py` uses `created_at`, not `created_date`
**Verify**: Run `test_sql_prompt_enhancements` test

### Issue: "Railway sector results are empty"
**Cause**: Railway doesn't exist in data; LLM generated query for it anyway
**Fix**: System prompt explicitly lists valid sectors; verify it's in the prompt
**Verify**: Check SYSTEM_PROMPT_SQL_GENERATION contains "NOT Railway"

### Issue: SQL executes but returns no data
**Cause**: Likely timestamp format or comparison issue
**Fix**: Verify timestamp parsing: `'2026-01-01T00:00:00Z'::TIMESTAMP` 
**Test**: Run manual query with correct timestamp format

### Issue: Insight generation is vague or generic
**Cause**: LLM not following insight prompt structure
**Fix**: Check `SYSTEM_PROMPT_INSIGHT_GENERATION` is being passed to LLM
**Verify**: Increase temperature slightly (0.1 → 0.2) for more narrative variation

### Issue: Frontend not showing up-to-date data
**Cause**: Data cached or Monday.com API not refreshing
**Fix**: Check Monday.com API connectivity; verify refresh strategy
**Debug**: Run `export_bi_snapshot.py` to see what data is live

---

## Next Steps for Executives

1. **Configure Monday.com Integration**
   - Set `MONDAY_API_TOKEN` (or MCP server URL)
   - Verify boards found: deals_pipeline, work_orders

2. **Test First Query**
   - Ask: "How many deals do we have?"
   - Verify: Returns count, not raw data dump
   - Check: System returns insight (e.g., "87 deals across 4 sectors, up 14% vs last quarter")

3. **Define Standard Questions**
   - Which questions does your CEO ask weekly?
   - Which reports do you need automated?
   - Add these to the system for baseline performance

4. **Iterate on Prompts**
   - Does the insight format match your needs?
   - Should we emphasize different angles (risk vs opportunity)?
   - Provide feedback for prompt refinement

5. **Plan Expansion**
   - New data sources? (Salesforce, HubSpot, etc.)
   - New analysis types? (Forecasting, cohort analysis, etc.)
   - Custom metrics? (Win rates, deal velocity, etc.)

---

## Support & Escalation

**Question about data**: Check `PRODUCTION_WORKFLOW_GUIDE.md` → Part 3 (Data Flow)

**Question about SQL generation**: Check `backend/sql/SQL_GENERATION_GUIDE.md` or run test suite

**Question about system prompts**: Check `backend/llm/` files or `foundation_prompts.py`

**Performance issue**: Profile query execution time; check Groq model latency

**Data missing**: Verify Monday.com board configuration; check data freshness

---

**Last Updated**: March 21, 2026  
**Version**: Production 1.0  
**Status**: Ready for Executive Deployment ✅
