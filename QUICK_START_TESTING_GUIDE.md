"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                    QUICK-START: TESTING & DEPLOYMENT                          ║
║                            IMMEDIATE NEXT STEPS                               ║
║                          March 21, 2026                                        ║
╚════════════════════════════════════════════════════════════════════════════════╝


📋 STEP-BY-STEP TEST EXECUTION (Copy-Paste Commands)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


STEP 1: Verify Data Loaded (2 minutes)
─────────────────────────────────────────────────────────────────────────────────

cd F:\\PyTorch_GPU\\Agentic_Monday_BI

python -c "
import pandas as pd
deals = pd.read_excel('f:/downloads_chrome/Deal funnel Data.xlsx', sheet_name='Deal tracker')
wo = pd.read_excel('f:/downloads_chrome/Work_Order_Tracker Data.xlsx', sheet_name='work order tracker', header=1)
print('✓ DEALS:', deals.shape, '- Columns:', list(deals.columns)[:3], '...')
print('✓ WORK ORDERS:', wo.shape, '- Columns:', list(wo.columns)[:3], '...')
print('✓ JOINS:', wo['Deal name masked'].nunique(), 'unique deals in WO matches', deals['Deal Name'].nunique(), 'unique deals in Deals')
"

Expected Output:
✓ DEALS: (346, 12)
✓ WORK ORDERS: (176, 38)
✓ JOINS: 58 unique deals in WO


STEP 2: Validate SQL Prompt Context (3 minutes)
─────────────────────────────────────────────────────────────────────────────────

python -m founder_bi_agent.backend.llm.test_sql_prompt_enhancements

Expected Output:
TEST 1: System Prompt Structure ✅ PASS (8/8)
TEST 2: Validation Hint ✅ PASS (5/5)
TEST 3: Table Metadata ✅ PASS (4/4)
TEST 4: SQL Patterns ✅ PASS (4/4)
OVERALL: ✅ ALL TESTS PASS (21/21)

If ❌ FAILS: Check sql_prompt_context.py has REAL column names (with quotes for spaces)


STEP 3: Run Comprehensive Test Suite (15 minutes)
─────────────────────────────────────────────────────────────────────────────────

python -c "
from scripts.comprehensive_test_plan import TEST_QUESTIONS, ADVANCED_QUESTIONS
print(f'Test Plan Loaded:')
print(f'  Core Questions: {len(TEST_QUESTIONS)}')
print(f'  Advanced Questions: {len(ADVANCED_QUESTIONS)}')
for q in TEST_QUESTIONS[:3]:
    print(f'  - {q[\"category\"]}: \"{q[\"question\"]}\"')
"

Expected Output:
Test Plan Loaded:
  Core Questions: 15
  Advanced Questions: 3
  - Pipeline Analysis: "What is the total deal value by sector?"
  ...


STEP 4: Test Sample SQL Queries (10 minutes)
─────────────────────────────────────────────────────────────────────────────────

python -c "
import duckdb
import pandas as pd

# Load test data
deals = pd.read_excel('f:/downloads_chrome/Deal funnel Data.xlsx', sheet_name='Deal tracker')
wo = pd.read_excel('f:/downloads_chrome/Work_Order_Tracker Data.xlsx', sheet_name='work order tracker', header=1)

# Register as DuckDB tables
conn = duckdb.connect(':memory:')
conn.register('deals', deals)
conn.register('work_orders', wo)

# Test Q1: Total deal value by sector
result = conn.execute('''
  SELECT \"Sector/service\", COUNT(*) as deal_count, SUM(\"Masked Deal value\") as total_value
  FROM deals
  WHERE \"Sector/service\" IS NOT NULL
  GROUP BY \"Sector/service\"
  ORDER BY total_value DESC
''').fetchall()

print('Q1: Deal Value by Sector')
for row in result[:5]:
    print(f'  {row[0]}: {row[1]} deals, ₹{row[2]:,.0f}')

# Test Q7: WO Value by Sector
result = conn.execute('''
  SELECT \"Sector\", COUNT(*) as wo_count, SUM(\"Amount in Rupees (Excl of GST) (Masked)\") as total_amount
  FROM work_orders
  GROUP BY \"Sector\"
  ORDER BY total_amount DESC
''').fetchall()

print()
print('Q7: Work Order Value by Sector')
for row in result:
    print(f'  {row[0]}: {row[1]} WOs, ₹{row[2]:,.0f}')

# Test Q11: Join - Deals with WOs
result = conn.execute('''
  SELECT d.\"Deal Name\", d.\"Sector/service\", d.\"Masked Deal value\", COUNT(wo.\"Deal name masked\") as wo_count
  FROM deals d
  LEFT JOIN work_orders wo ON d.\"Deal Name\" = wo.\"Deal name masked\"
  GROUP BY d.\"Deal Name\", d.\"Sector/service\", d.\"Masked Deal value\"
  LIMIT 5
''').fetchall()

print()
print('Q11: Deal to WO Join (Sample)')
for row in result:
    print(f'  {row[0]}: {row[1]}, ₹{row[2]:,.0f}, WOs: {row[3]}')
"

Expected Output:
Q1: Deal Value by Sector
  Mining: X deals, ₹Y
  Powerline: X deals, ₹Y
  ...

Q7: Work Order Value by Sector
  Mining: X WOs, ₹Y
  ...

Q11: Deal to WO Join (Sample)
  Deal_Name: Sector, ₹Value, WOs: Count
  ...


STEP 5: Performance Baseline (5 minutes)
─────────────────────────────────────────────────────────────────────────────────

python << 'EOF'
import duckdb
import pandas as pd
import time

deals = pd.read_excel('f:/downloads_chrome/Deal funnel Data.xlsx', sheet_name='Deal tracker')
wo = pd.read_excel('f:/downloads_chrome/Work_Order_Tracker Data.xlsx', sheet_name='work order tracker', header=1)

conn = duckdb.connect(':memory:')
conn.register('deals', deals)
conn.register('work_orders', wo)

queries = [
    ("Q1 (Simple GROUP BY)", 'SELECT "Sector/service", SUM("Masked Deal value") FROM deals GROUP BY "Sector/service"'),
    ("Q4 (Date filter)", 'SELECT COUNT(*) FROM deals WHERE CAST("Tentative Close Date" AS DATE) >= CAST(\'2026-01-01\' AS DATE)'),
    ("Q11 (JOIN)", 'SELECT d."Deal Name", COUNT(wo."Deal name masked") FROM deals d LEFT JOIN work_orders wo ON d."Deal Name" = wo."Deal name masked" GROUP BY d."Deal Name"'),
]

print("Performance Baseline (3 iterations each):")
for name, query in queries:
    times = []
    for _ in range(3):
        start = time.time()
        conn.execute(query)
        times.append((time.time() - start) * 1000)  # ms
    
    avg_ms = sum(times) / len(times)
    print(f"  {name}: {avg_ms:.1f}ms" + (" ✅ GOOD" if avg_ms < 100 else " ⚠️  Check"))

print("\nTarget: <100ms average, <500ms max")
EOF

Expected Output:
Performance Baseline (3 iterations each):
  Q1 (Simple GROUP BY): X.Xms ✅ GOOD
  Q4 (Date filter): X.Xms ✅ GOOD
  Q11 (JOIN): X.Xms ✅ GOOD

Target: <100ms average, <500ms max


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ IF ALL STEPS PASS → READY FOR DEPLOYMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


DEPLOYMENT READY CHECKLIST

Pre-Deployment (Founder + Tech Lead):
  □ Review EXECUTIVE_SUMMARY_& _LAUNCH_ROADMAP.md
  □ Verify data validation (Step 1) ✅
  □ Confirm SQL prompt tests (Step 2) ✅
  □ Check performance baseline (Step 5) <100ms ✓
  □ Review sample SQL results (Step 4) - Accuracy OK? ✓
  □ Get executive approval to proceed


Deployment Window: 2-4 hours
  9:00am  - Pre-flight checks
  9:30am  - Deploy to staging
  10:00am - Run 5 critical tests
  10:30am - Founder approval
  11:00am - Deploy to production
  11:30am - Monitor intensively for 2 hours
  1:30pm  - Go live + user notification


Post-Deployment:
  □ Monitor error rate (should be <2%)
  □ Track avg latency (should be <100ms)
  □ Collect early user feedback
  □ Daily standup for first week


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 TEST RESULTS TRACKER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use this form to track your test execution:

Date: ___________  Tester: ___________  Time: ___________

STEP 1 - Data Validation:
  □ Deals loaded: 346 rows ✅
  □ Work Orders loaded: 176 rows ✅
  □ Join key validated ✅
  Result: PASS / FAIL    Time: ___ min

STEP 2 - SQL Prompt Tests:
  □ System Prompt: 8/8 ✅
  □ Validation Hint: 5/5 ✅
  □ Table Metadata: 4/4 ✅
  □ SQL Patterns: 4/4 ✅
  Result: PASS (21/21) / FAIL    Time: ___ min

STEP 3 - Test Plan Review:
  □ Core Questions: 15 loaded ✅
  □ Advanced Questions: 3 loaded ✅
  Result: PASS / FAIL    Time: ___ min

STEP 4 - Sample SQL Queries:
  □ Q1 (Simple): ✅ Correct results
  □ Q7 (Sector): ✅ Correct results
  □ Q11 (Join): ✅ Correct results
  Result: PASS 3/3 / FAIL    Time: ___ min

STEP 5 - Performance Baseline:
  □ Average latency: ___ ms (target <100ms)
  □ Max latency: ___ ms (target <500ms)
  □ Memory stable: Yes / No
  Result: PASS / FAIL    Time: ___ min


OVERALL RESULT: ___________

Approval to Deploy: YES / NO

Signed: ________________  Date: __________


═════════════════════════════════════════════════════════════════════════════════
                              Ready for Production
                            Execute steps 1-5 above
                          All tests should pass before deploying
═════════════════════════════════════════════════════════════════════════════════
"""
