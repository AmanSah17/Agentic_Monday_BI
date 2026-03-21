"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                  BACKEND ERROR FIX & PROPER QUESTION FORMAT                    ║
║                              Quick Reference                                   ║
║                           March 21, 2026                                       ║
╚════════════════════════════════════════════════════════════════════════════════╝


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ ERROR YOU ENCOUNTERED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Backend query failed (422): 
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "question"],
      "msg": "String should have at least 3 characters",
      "input": "no",
      "ctx": {"min_length": 3}
    }
  ]
}

ROOT CAUSE: Your question was "no" (2 characters)
The backend API requires a MINIMUM of 3 characters per question.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ FIX: USE PROPER QUESTION FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULE: Questions MUST be at least 3 characters long

❌ INVALID (Too Short):
  • "no" (2 chars)
  • "yes" (3 chars, but too vague)
  • "ok" (2 chars)
  • "Q5" (2 chars)
  • "Q6" (2 chars)

✅ VALID (3+ Characters, Clear):
  • "What is our pipeline by sector?" (34 chars)
  • "Deals by owner: who has the most value in pipeline?" (51 chars)
  • "What's the status breakdown of work orders by execution?" (58 chars)
  • "Tell me about Q5" (15 chars)
  • "Can you explain question 5?" (27 chars)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 PROPER QUESTIONS 5-6 TO USE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUESTION 5 (RECOMMENDED PHRASING):
────────────────────────────────────

Proper Format:
  "Deals by owner: who has the most value in pipeline?"
  (51 characters ✅)

Alternative Phrasings:
  • "Which sales owner has the largest deal pipeline?" (49 chars)
  • "Sales owner ranking by pipeline value" (38 chars)
  • "Who is our top performing sales owner by deal value?" (52 chars)
  • "Owner performance: pipeline value ranking" (41 chars)

Expected Data Response:
┌─────────────┬──────────────┬──────────────────────┬──────────────┐
│ Owner Code  │ Deal Count   │ Total Pipeline Value │ % of Total   │
├─────────────┼──────────────┼──────────────────────┼──────────────┤
│ OWNER_003   │ 95 deals     │ ₹580.5M             │ 25.2%        │
│ OWNER_001   │ 87 deals     │ ₹520.3M             │ 22.6%        │
│ OWNER_002   │ 63 deals     │ ₹412.6M             │ 17.9%        │
└─────────────┴──────────────┴──────────────────────┴──────────────┘

Expected Insight Format:
  ✓ HEADLINE: Who leads, by how much, key insight
  ✓ KEY METRICS: Quantitative data with context
  ✓ ANALYSIS: What does this mean for business
  ✓ RISKS: What could go wrong
  ✓ RECOMMENDATIONS: What to do about it


QUESTION 6 (RECOMMENDED PHRASING):
────────────────────────────────────

Proper Format:
  "What's the status breakdown of work orders by execution?"
  (58 characters ✅)

Alternative Phrasings:
  • "Work order execution status summary" (35 chars)
  • "How many work orders are completed vs ongoing?" (47 chars)
  • "WO execution status breakdown" (29 chars)
  • "Work order progress by execution status" (39 chars)

Expected Data Response:
┌────────────────────────────┬────────┬──────────┬──────────────┐
│ Execution Status           │ Count  │ % Total  │ Amount (₹M)  │
├────────────────────────────┼────────┼──────────┼──────────────┤
│ Completed                  │ 72 WOs │ 40.9%    │ ₹133.2M      │
│ Executed until current mo  │ 31 WOs │ 17.6%    │ ₹37.4M       │
│ Ongoing                    │ 28 WOs │ 15.9%    │ ₹37.5M       │
│ Not Started                │ 22 WOs │ 12.5%    │ ₹20.9M       │
│ Partial Completed          │ 12 WOs │ 6.8%     │ ₹10.7M       │
│ Details pending from Clien │ 9 WOs  │ 5.1%     │ ₹3.1M        │
│ Pause / struck             │ 2 WOs  │ 1.1%     │ ₹0.3M        │
└────────────────────────────┴────────┴──────────┴──────────────┘

Expected Insight Format:
  ✓ HEADLINE: Completion rate, money at risk
  ✓ METRICS: Stage breakdown, revenue impact
  ✓ ANALYSIS: Healthy execution velocity? Bottlenecks?
  ✓ RISKS: Stalled projects, blocked resources
  ✓ RECOMMENDATIONS: Unblock clients, prioritize, reallocate


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 HOW TO USE IN CHAT INTERFACE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Open Chat Interface
  Location: http://localhost:5173 (frontend)

Step 2: Type Full Question (3+ chars minimum)
  ❌ WRONG: Type "Q5"
  ✅ RIGHT: Type "Deals by owner: who has the most value in pipeline?"

Step 3: Press Send / Enter
  System processes:
  1. Question validation (minimum 3 chars) ✅
  2. Intent classification (TEAM_PERFORMANCE)
  3. Schema discovery (fetch Deal/Owner data)
  4. SQL generation (GROUP BY owner, SUM value)
  5. Query execution (DuckDB, <50ms)
  6. Insight transformation (CEO format)
  7. Display to user

Step 4: Review Response
  Expected format:
  ┌────────────────────────────────┐
  │ HEADLINE                       │
  │                                │
  │ KEY METRICS                    │
  │ • Metric 1: Value             │
  │ • Metric 2: Value             │
  │                                │
  │ BUSINESS ANALYSIS              │
  │ [2-3 paragraph explanation]    │
  │                                │
  │ RISKS & OPPORTUNITIES          │
  │ ⚠️  Risk 1                     │
  │ ✓  Opportunity 1               │
  │                                │
  │ RECOMMENDATIONS                │
  │ 1. Action 1                   │
  │ 2. Action 2                   │
  └────────────────────────────────┘


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 SAMPLE QUESTIONS 5-6 FULL RESPONSES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUESTION 5 - Full Expected Response:
────────────────────────────────────

User Input:
  "Deals by owner: who has the most value in pipeline?"

System Response (Executive Summary):

HEADLINE:
OWNER_003 leads sales pipeline with ₹580M (25% of total), followed by OWNER_001 
(₹520M). Wide performance gap indicates concentration risk - top 2 owners represent 
48% of total pipeline.

KEY METRICS:
• Top Owner (OWNER_003): ₹580M across 95 deals
• Second (OWNER_001): ₹520M across 87 deals
• Average per owner: ₹330M
• Median per owner: ₹295M
• Performance spread: 13x difference (₹580M vs ₹45M)
• Concentration: Top 3 owners = 66% of total pipeline

BUSINESS ANALYSIS:
This distribution shows healthy sales force but with concentration risk. OWNER_003 
and OWNER_001 are clearly top performers with strong deal flow. However, if either 
owner leaves or has capacity issues, pipeline could be significantly impacted.

OWNER_002-OWNER_004 represent solid mid-tier performers (₹380-413M each). OWNER_005 
underperforms relative to peer group (₹212M). OWNER_007 appears to be new hire or 
has engagement issues (only 2 deals, ₹45M).

RISKS & OPPORTUNITIES:
⚠️  Risk 1: Owner concentration - if top 2 owners unavailable, lose ₹1.1B (48%)
⚠️  Risk 2: OWNER_005 underperformance relative to peers
⚠️  Risk 3: OWNER_007 onboarding/engagement - minimal pipeline
✓  Opportunity 1: Replicate OWNER_003 success patterns and process
✓  Opportunity 2: Mentor OWNER_005 through pairing with OWNER_003

RECOMMENDATIONS:
1. IMMEDIATE: Pair OWNER_005 with OWNER_003 for 4-week coaching/mentorship
2. Analyze OWNER_003's sector focus (likely Mining, best conversion rate)
3. Investigate OWNER_007 status - new hire support needed or performance issue?
4. Rebalance deal allocation to reduce top-owner concentration
5. Set growth targets: OWNER_005 from ₹212M to ₹350M+ by Q3 2026
6. Document OWNER_003's successful sales process for team replication


QUESTION 6 - Full Expected Response:
────────────────────────────────────

User Input:
  "What's the status breakdown of work orders by execution?"

System Response (Executive Summary):

HEADLINE:
41% of work orders (72/176) are completed, generating ₹133M in revenue. An additional 
34% are in progress (on track). However, 19% are at immediate risk: 22 not started, 
9 pending client details, 2 struck/paused.

KEY METRICS:
• Completed: 72 WOs (40.9%) = ₹133.2M ✅ (healthy revenue)
• In Progress: 59 WOs (33.5%) = ₹74.9M (on track to completion)
  - Executed until current month: 31 WOs = ₹37.4M
  - Ongoing: 28 WOs = ₹37.5M
• At Risk: 33 WOs (18.8%) = ₹24.1M ⚠️
  - Not Started: 22 WOs = ₹20.9M (concerning delay)
  - Pending Client Details: 9 WOs = ₹3.1M (unblockable with follow-up)
  - Paused/Struck: 2 WOs = ₹0.3M (investigate blocker)

Average project value: ₹1.2M
Total pipeline value: ₹212M

BUSINESS ANALYSIS:
Execution velocity is healthy for a services business - 41% completion represents 
good progress toward revenue recognition. The "Executed until current month" category 
(31 WOs) indicates well-functioning recurring project management.

Concern: 22 work orders "Not Started" (12.5% of portfolio, ₹21M) suggests either:
  a) Resource constraint (can't allocate team)
  b) Client delay (waiting for LOI, PO, or approvals)
  c) Planning issue (scope not finalized)

Opportunity: 9 pending client details (₹3M) can likely be unblocked with proactive 
follow-up to client.

RISKS & OPPORTUNITIES:
⚠️  Risk 1: Not Started (22 WOs, ₹21M) - if continues, could delay revenue by 1-2Q
⚠️  Risk 2: Client Pending (9 WOs, ₹3M) - stalled waiting on approvals
⚠️  Risk 3: Execution bottleneck if resource-constrained (can't staff projects)
✓  Opportunity 1: Unblock pending client details - likely 80% success in 1 week
✓  Opportunity 2: Accelerate "Executed until" WOs to Completed status (+₹37M)
✓  Opportunity 3: Prioritize Not Started projects - could accelerate ₹10-15M

RECOMMENDATIONS:
1. URGENT: Root cause analysis of 22 "Not Started" WOs - survey project managers
2. CLIENT OUTREACH: Follow up on 9 pending client details - schedule calls this week
3. RESOURCE PLANNING: If constraint, plan hiring or contract resources for Q2
4. PRIORITIZATION: Rank Not Started WOs - accelerate top 10 (₹15M potential)
5. FORECAST: If velocity maintained, ₹185M (87%) will be completed by Q3 end
   - Target: Improve to 95% completion by Q3 (= ₹201M)
6. ESTABLISH SLA: "Not Started" WOs should start within 2 weeks of LOI


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ QUICK COPY-PASTE QUESTIONS (READY TO USE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Copy and paste these directly into chat (minimum 3 characters guaranteed):

Q1: What is the total deal value by sector?
Q2: How many deals are in each stage?
Q3: What deals are open and what's their total value?
Q4: What is our Q1 2026 pipeline by sector and deal status?
Q5: Deals by owner: who has the most value in pipeline?
Q6: What's the status breakdown of work orders by execution?
Q7: What is the total work order revenue by sector?
Q8: How many work orders are completed versus ongoing?
Q9: What is the billing versus collection gap in work orders?
Q10: Work order breakdown by nature of work and execution status
Q11: Which deals have corresponding work orders and what's the value difference?
Q12: For completed work orders, what is the deal-to-revenue conversion by sector?
Q13: Can you show the deal-to-revenue funnel from pipeline value to collected amount?
Q14: What are the top 10 deals by value and their work order status?
Q15: Which deals do not have corresponding work orders and what is the value at risk?


═════════════════════════════════════════════════════════════════════════════════

KEY TAKEAWAYS:

1. Always use questions LONGER than 3 characters
2. Use full, complete question sentences
3. Avoid single-word or two-letter answers
4. The system will respond with structured insights in format:
   HEADLINE → KEY METRICS → ANALYSIS → RISKS → RECOMMENDATIONS
5. If you get "String should have at least 3 characters" error, rephrase your question

QUESTIONS 5-6 ARE READY TO USE NOW (51 and 58 characters respectively)

═════════════════════════════════════════════════════════════════════════════════
"""
