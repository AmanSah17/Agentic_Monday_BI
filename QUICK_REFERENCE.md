# 🎯 QUICK REFERENCE - Deal Tracker Integration

## 📍 You Are Here
**Completed**: All 28 columns documented, Dashboard integrated, Reasoning guide ready  
**Team Ready**: Yes, with comprehensive documentation  
**Next**: Field extraction implementation (follow REASONING_MODEL_ENHANCEMENT.md)

---

## 🔗 Key Files - Where to Find Everything

### Column Reference (All 28 Columns)
```
📄 DEAL_TRACKER_COLUMNS.md
   └─ All column names, types, ranges, examples
   └─ SQL queries for different use cases
   └─ User-friendly to database mappings
```

### Frontend Dashboard Integration
```
📁 founder_bi_agent/frontend/src/
   ├─ App.tsx (viewMode state + conditional render)
   ├─ components/
   │  ├─ Sidebar.tsx (navigation with 5 views)
   │  └─ AnalyticsDashboard.tsx (6 charts)
```

### Backend Metadata
```
📁 founder_bi_agent/backend/sql/
   └─ table_metadata.py (all 28 columns documented)
```

### Implementation Guide
```
📄 REASONING_MODEL_ENHANCEMENT.md
   ├─ Field extractor (ready to code)
   ├─ Clarification engine (ready to code)
   ├─ Column mapper (ready to code)
   └─ Integration examples
```

---

## 🏃 30-Second Test

### Check Dashboard Works
```bash
# Terminal 1: Start backend
python -m uvicorn founder_bi_agent.backend.api:app --port 8010 --reload

# Terminal 2: Start frontend
cd founder_bi_agent/frontend && npm run dev

# Browser: Open http://localhost:3000
# Click "Dashboard" button → See 6 charts
```

**Expected**: 6 charts load with real data from Monday.com

---

## 📋 The 28 Deal Columns

```
1. item_id                    | Unique ID
2. item_name                  | Deal name
3. created_at                 | System creation time
4. updated_at                 | Last update time
5. group_id                   | Category ID
6. group_title                | Category name
7. owner_code                 | Sales owner
8. owner_code__raw            | Raw owner (JSON)
9. client_code                | Client/Company
10. client_code__raw          | Raw client (JSON)
11. deal_status               | Open/Won/Lost/On Hold
12. deal_status__raw          | Raw status (JSON)
13. close_date_a              | Deal close date
14. close_date_a__raw         | Raw close date (JSON)
15. closure_probability       | High/Medium/Low
16. closure_probability__raw  | Raw probability (JSON)
17. masked_deal_value         | Value (₹)
18. masked_deal_value__raw    | Raw value (JSON)
19. tentative_close_date      | Projected close
20. tentative_close_date__raw | Raw tentative (JSON)
21. deal_stage                | Pipeline stage A-M
22. deal_stage__raw           | Raw stage (JSON)
23. product_deal              | Product/service type
24. product_deal__raw         | Raw product (JSON)
25. sectorservice             | Mining/Powerline/...
26. sectorservice__raw        | Raw sector (JSON)
27. created_date              | Creation date
28. created_date__raw         | Raw creation (JSON)
```

---

## 🎮 Frontend Navigation (Now Working)

```
┌─────────────────────────────────────────┐
│  Executive Intelligence                 │ ← Sidebar
├─────────────────────────────────────────┤
│ ⊙ Chat              (currently active)  │
│ ◦ Dashboard         (6 charts)          │
│ ◦ Data Map          (placeholder)       │
│ ◦ Library           (placeholder)       │
│ ◦ Admin             (placeholder)       │
└─────────────────────────────────────────┘
```

Click any button → View switches instantly

---

## 📊 What Dashboard Shows (6 Charts)

```
1. Deals by Stage (Bar)
   └─ How many deals in each pipeline stage

2. Revenue by Sector (Pie)
   └─ What % of value in Mining, Powerline, etc.

3. Work Orders by Status (Bar)
   └─ Distribution across execution statuses

4. Monthly Revenue Trends (Line)
   └─ Project value, billed, collected over time

5. Deal Status Distribution (Pie)
   └─ Open, Won, Lost, On Hold breakdown

6. Monthly Deals Created (Line)
   └─ Trend of deal creation rate
```

---

## 🔨 Next Tasks (In Order)

### Task 1: Verify Install (5 min)
- [ ] Run backend: `python -m uvicorn founder_bi_agent.backend.api:app --port 8010 --reload`
- [ ] Run frontend: `npm run dev` in `founder_bi_agent/frontend`
- [ ] Click "Dashboard" - see 6 charts

### Task 2: Field Extraction (4-6 hours)
- [ ] Create `backend/graph/field_extractor.py` (copy from guide)
- [ ] Create `backend/graph/clarification_engine.py` (copy from guide)
- [ ] Test with `scripts/test_field_extraction.py`

### Task 3: Integration (1-2 hours)
- [ ] Update `backend/graph/nodes.py` reasoning node
- [ ] Add field extraction logic
- [ ] Add clarification logic

### Task 4: Testing (1 hour)
- [ ] Send queries to backend
- [ ] Verify field extraction works
- [ ] Verify clarifications show when needed

---

## 💡 Key Insights

**The Mismatch You Found**:
- SQL showed basic columns from information_schema
- Actual dataframe had 28 columns with Monday.com structure
- **Solution**: Updated metadata to match actual data

**Column Pattern**:
- Every major field comes in pairs: `column_name` + `column_name__raw`
- Display columns are cleaned, raw columns preserve JSON structure
- Users see clean columns, system uses both

**Frontend Success**:
- Navigation now switches between 5 views
- Dashboard no longer buried in one view
- Each view can be extended independently

---

## 🚀 Commands You'll Use

### Start Development
```bash
# Terminal 1: Backend
python -m uvicorn founder_bi_agent.backend.api:app --port 8010 --reload

# Terminal 2: Frontend  
cd founder_bi_agent/frontend && npm run dev

# Browser
open http://localhost:3000
```

### Test Column Access
```bash
python -c "from founder_bi_agent.backend.sql.table_metadata import DEALS_METADATA; print(len(DEALS_METADATA.all_columns))"
# Output: 28
```

### View Columns
```bash
python -c "from founder_bi_agent.backend.sql.table_metadata import DEALS_METADATA; print('\n'.join(DEALS_METADATA.all_columns))"
```

### Test Field Extraction (After Implementation)
```bash
python scripts/test_field_extraction.py
```

---

## ✅ Completion Checklist

- [x] All 28 columns documented
- [x] Data ranges recorded (346 rows, ₹305K-₹305M)
- [x] Backend metadata updated
- [x] Frontend dashboard integrated
- [x] Navigation system working
- [x] 6 visualizations functional
- [x] Field extraction guide written
- [x] Clarification engine designed
- [x] Implementation examples provided
- [x] Team documentation complete

---

## 🎯 Success Criteria

✅ **Can you follow this checklist?**
1. [ ] View all 28 columns: `DEAL_TRACKER_COLUMNS.md` ✓
2. [ ] Access dashboard: Click "Dashboard" button ✓
3. [ ] See 6 charts: Line, bar, pie charts render ✓
4. [ ] Understand next steps: Read REASONING_MODEL_ENHANCEMENT.md ✓

**If all checked** → Integration successful!

---

## 📞 Got Questions?

| Question | Answer In |
|----------|-----------|
| What are all 28 columns? | DEAL_TRACKER_COLUMNS.md |
| How do I see the dashboard? | Click Dashboard button |
| What does each chart show? | COMPLETE_STATUS_REPORT.md |
| How do I add field extraction? | REASONING_MODEL_ENHANCEMENT.md |
| How do I see data ranges? | DEAL_TRACKER_COLUMNS.md table |
| How do I query the data? | DEAL_TRACKER_COLUMNS.md (SQL section) |
| How does navigation work? | App.tsx |
| What's the team workflow? | GIT_WORKFLOW_REFERENCE.md |

---

**Status**: ✅ READY TO USE  
**Team**: ✅ FULLY DOCUMENTED  
**Next Phase**: FIELD EXTRACTION  
**Estimated Time**: 4-6 hours for next phase  

You have everything you need. Start with the 30-second test! 🚀
