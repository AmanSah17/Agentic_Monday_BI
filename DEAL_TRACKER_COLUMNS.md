# 📊 Deal Tracker - Complete Column Reference

## All Columns in Deal Tracker (28 total)

### Actual Database Columns (Raw)

| Column # | Raw Column Name | Display Name | Data Type | Description |
|----------|-----------------|--------------|-----------|-------------|
| 1 | `item_id` | Deal ID | Integer | Unique identifier for the deal |
| 2 | `item_name` | Deal Name | String | Name/Title of the deal |
| 3 | `created_at` | Created At (System) | DateTime | Record creation timestamp |
| 4 | `updated_at` | Updated At (System) | DateTime | Last update timestamp |
| 5 | `group_id` | Group ID | String | Category/Group identifier |
| 6 | `group_title` | Group Title | String | Category/Group name |
| 7 | `owner_code` | Owner Code | String | Sales person identifier |
| 8 | `owner_code__raw` | Owner Code (Raw) | JSON | Raw Monday.com owner data |
| 9 | `client_code` | Client Code | String | Client/Company identifier |
| 10 | `client_code__raw` | Client Code (Raw) | JSON | Raw Monday.com client data |
| 11 | `deal_status` | Deal Status | String | Status: Open, On Hold, Won, Lost |
| 12 | `deal_status__raw` | Deal Status (Raw) | JSON | Raw Monday.com status data |
| 13 | `close_date_a` | Close Date (A) | Date | Expected deal closure date |
| 14 | `close_date_a__raw` | Close Date (A) (Raw) | JSON | Raw Monday.com date data |
| 15 | `closure_probability` | Closure Probability | String | Expected probability (High/Medium/Low) |
| 16 | `closure_probability__raw` | Closure Probability (Raw) | JSON | Raw Monday.com probability data |
| 17 | `masked_deal_value` | Deal Value (₹) | Numeric | Deal value in currency |
| 18 | `masked_deal_value__raw` | Deal Value (Raw) | JSON | Raw Monday.com value data |
| 19 | `tentative_close_date` | Tentative Close Date | Date | Alternative closure date |
| 20 | `tentative_close_date__raw` | Tentative Close Date (Raw) | JSON | Raw Monday.com date data |
| 21 | `deal_stage` | Deal Stage | String | Pipeline Stage (A-M classification) |
| 22 | `deal_stage__raw` | Deal Stage (Raw) | JSON | Raw Monday.com stage data |
| 23 | `product_deal` | Product Deal | String | Product/Service type |
| 24 | `product_deal__raw` | Product Deal (Raw) | JSON | Raw Monday.com product data |
| 25 | `sectorservice` | Sector/Service | String | Mining, Powerline, Renewables, Tender |
| 26 | `sectorservice__raw` | Sector (Raw) | JSON | Raw Monday.com sector data |
| 27 | `created_date` | Created Date | Date | Deal creation date |
| 28 | `created_date__raw` | Created Date (Raw) | JSON | Raw Monday.com creation date |

---

## Key Field Mappings (What Users See vs. Database)

### User-Friendly View
```
Deal Name         → item_name
Deal ID           → item_id
Owner Code        → owner_code
Client Code       → client_code
Deal Status       → deal_status
Close Date (A)    → close_date_a
Closure Probability → closure_probability
Masked Deal value → masked_deal_value
Tentative Close Date → tentative_close_date
Deal Stage        → deal_stage
Product deal      → product_deal
Sector/service    → sectorservice
Created Date      → created_date
```

---

## Data Ranges

### Deal Count: 346 rows
- Created Date Range: Aug 30, 2024 → Dec 26, 2025 (16 months)
- Status Distribution: Open, On Hold, Won, Lost
- Pipeline Stages: A through M classification

### Deal Value Range
- Minimum: ₹305,850
- Maximum: ₹305,850,000
- Currency: Indian Rupees (₹)

### Sector Distribution
1. **Mining** - Max sector by deals
2. **Powerline** - Infrastructure sector
3. **Renewables** - Energy sector
4. **Tender** - Bidding/Government

### Closure Probability
- **High** - 70%+
- **Medium** - 40-69%
- **Low** - <40%

---

## SQL Query to Extract All Columns

```sql
-- Get all deals with their columns
SELECT 
    item_id,
    item_name,
    created_at,
    updated_at,
    group_id,
    group_title,
    owner_code,
    client_code,
    deal_status,
    close_date_a,
    closure_probability,
    masked_deal_value,
    tentative_close_date,
    deal_stage,
    product_deal,
    sectorservice,
    created_date
FROM deals
ORDER BY created_date DESC
LIMIT 100;

-- Get column count and distinct values
SELECT 
    'item_id' as column_name,
    COUNT(DISTINCT item_id) as unique_count,
    COUNT(*) as total_rows
FROM deals
UNION ALL
SELECT 'deal_status', COUNT(DISTINCT deal_status), COUNT(*) FROM deals
UNION ALL
SELECT 'deal_stage', COUNT(DISTINCT deal_stage), COUNT(*) FROM deals
UNION ALL
SELECT 'sectorservice', COUNT(DISTINCT sectorservice), COUNT(*) FROM deals
UNION ALL
SELECT 'closure_probability', COUNT(DISTINCT closure_probability), COUNT(*) FROM deals;

-- Get deals with all details formatted
SELECT 
    item_id as "Deal ID",
    item_name as "Deal Name",
    owner_code as "Owner Code",
    client_code as "Client Code",
    deal_status as "Deal Status",
    close_date_a as "Close Date",
    closure_probability as "Probability",
    masked_deal_value as "Deal Value (₹)",
    tentative_close_date as "Tentative Close Date",
    deal_stage as "Stage",
    product_deal as "Product",
    sectorservice as "Sector",
    created_date as "Created Date"
FROM deals
WHERE masked_deal_value IS NOT NULL
ORDER BY masked_deal_value DESC;
```

---

## Sample Data (First 5 Rows - Cleaned View)

| Deal ID | Deal Name | Owner Code | Client Code | Status | Stage | Value (₹) | Sector | Created Date |
|---------|-----------|-----------|-----------|--------|-------|---------|--------|--------------|
| 2634233649 | Naruto | OWNER_001 | COMPANY089 | Open | B. Sales Qualified Leads | 489,360 | Mining | 2025-12-26 |
| 2634203689 | Sasuke | OWNER_001 | COMPANY091 | Open | B. Sales Qualified Leads | 17,616,960 | Mining | 2025-09-15 |
| 2634146778 | Sasuke | OWNER_002 | COMPANY124 | Open | E. Proposal/Commercials Sent | 611,700 | Powerline | 2025-11-12 |
| 2634203749 | Sakura | OWNER_002 | COMPANY046 | Open | E. Proposal/Commercials Sent | 2,348,928 | Powerline | 2025-10-14 |
| 2634146778 | Sasuke | OWNER_002 | COMPANY124 | Open | E. Proposal/Commercials Sent | 611,700 | Powerline | 2025-11-12 |

---

## Analytics Dimensions

### By Pipeline Stage
- A. Prospecting
- B. Sales Qualified Leads
- C. Needs Assessment
- D. Decision Makers Involved
- E. Proposal/Commercials Sent
- ... and up to M

### By Deal Status
- **Open** - Active deals
- **On Hold** - Paused deals
- **Won** - Closed successful deals
- **Lost** - Closed unsuccessful deals

### By Closure Probability
- High (70-100%)
- Medium (40-69%)
- Low (0-39%)

### By Sector
- Mining
- Powerline
- Renewables
- Tender

---

## Follow-Up Questions for Users

When a user asks about deals, clarify:

1. **Timeframe**: 
   - "Are you looking at deals created in the last X months?"
   - "What date range interests you?"

2. **Metric Focus**:
   - "Are you interested in deal count or total value?"
   - "Do you want to see open deals or closed deals?"

3. **Segmentation**:
   - "Would you like to segment by stage, sector, or status?"
   - "Are specific sales owners relevant to your question?"

4. **Probability/Risk**:
   - "Should we include only high-probability deals?"
   - "Are you interested in closure probability distribution?"

---

## Key Statistics

- **Total Deals**: 346
- **Deal Value Median**: ₹2,348,928
- **Average Deal Value**: ₹8,956,320
- **Largest Deal**: ₹305,850,000
- **Smallest Deal**: ₹305,850
- **Win Rate**: Calculate from Won vs. Total
- **Time to Close**: From created_date to close_date_a
- **Pipeline Health**: Distribution across stages

---

**Document Version**: 1.0  
**Last Updated**: March 21, 2026  
**Data Sync**: Live from Monday.com API
