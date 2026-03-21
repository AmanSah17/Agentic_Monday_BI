"""
FOUNDER BI AGENT - COMPREHENSIVE TEST PLAN
Real Data Calibration with 15 Sample CEO Questions
March 21, 2026

This test suite simulates real CEO/CTO questions against actual Monday.com data
from Deal funnel Data.xlsx and Work_Order_Tracker Data.xlsx
"""

TEST_QUESTIONS = [
    # ========================================================================
    # GROUP A: PIPELINE & DEAL ANALYSIS (5 questions)
    # ========================================================================
    {
        "id": "Q1",
        "category": "Pipeline Analysis",
        "difficulty": "Easy",
        "question": "What is the total deal value by sector?",
        "expected_sql_pattern": ['SELECT "Sector/service", SUM("Masked Deal value")', 'GROUP BY "Sector/service"'],
        "expected_output": "DataFrame with sectors and total values",
        "data_context": "346 deals, ₹2.3B total, 12 sectors",
        "production_metrics": {
            "expected_rows": 12,
            "expected_columns": 2,
            "execution_time_estimate_ms": 10
        }
    },
    {
        "id": "Q2",
        "category": "Pipeline Analysis",
        "difficulty": "Easy",
        "question": "How many deals are in each stage?",
        "expected_sql_pattern": ['SELECT "Deal Stage", COUNT(*)', 'GROUP BY "Deal Stage"', 'ORDER BY COUNT(*) DESC'],
        "expected_output": "Deal stage breakdown with counts",
        "data_context": "17 unique deal stages, 346 deals",
        "production_metrics": {
            "expected_rows": 17,
            "expected_columns": 2,
            "execution_time_estimate_ms": 8
        }
    },
    {
        "id": "Q3",
        "category": "Pipeline Analysis",
        "difficulty": "Medium",
        "question": "What deals are open and what's their total value?",
        "expected_sql_pattern": ['WHERE "Deal Status" = \'Open\'', 'SUM("Masked Deal value")'],
        "expected_output": "Count and total value of open deals",
        "data_context": "Multiple deals with 'Open' status",
        "production_metrics": {
            "expected_rows": 1,
            "expected_columns": 2,
            "execution_time_estimate_ms": 8
        }
    },
    {
        "id": "Q4",
        "category": "Pipeline Analysis",
        "difficulty": "Hard",
        "question": "Q1 2026 (Jan-Mar) pipeline: total value by sector and status",
        "expected_sql_pattern": ['CAST("Tentative Close Date" AS DATE) >= \'2026-01-01\'', 'GROUP BY "Sector/service", "Deal Status"'],
        "expected_output": "Matrix: sectors x status with values",
        "data_context": "Date filtering required, multiple criteria",
        "production_metrics": {
            "expected_rows": "~30-40",
            "expected_columns": 3,
            "execution_time_estimate_ms": 12
        }
    },
    {
        "id": "Q5",
        "category": "Pipeline Analysis",
        "difficulty": "Hard",
        "question": "Deals by owner: who has the most value in pipeline?",
        "expected_sql_pattern": ['SELECT "Owner code", SUM("Masked Deal value")', 'GROUP BY "Owner code"', 'ORDER BY SUM desc'],
        "expected_output": "Owner rankings by deal value",
        "data_context": "7 owners, need aggregation",
        "production_metrics": {
            "expected_rows": 7,
            "expected_columns": 2,
            "execution_time_estimate_ms": 10
        }
    },
    
    # ========================================================================
    # GROUP B: WORK ORDER ANALYSIS (5 questions)
    # ========================================================================
    {
        "id": "Q6",
        "category": "Work Order",
        "difficulty": "Easy",
        "question": "What's the status breakdown of work orders by execution?",
        "expected_sql_pattern": ['SELECT "Execution Status", COUNT(*)', 'FROM work_orders', 'GROUP BY "Execution Status"'],
        "expected_output": "Execution status counts (7 values)",
        "data_context": "176 work orders, 7 execution statuses",
        "production_metrics": {
            "expected_rows": 7,
            "expected_columns": 2,
            "execution_time_estimate_ms": 6
        }
    },
    {
        "id": "Q7",
        "category": "Work Order",
        "difficulty": "Easy",
        "question": "Total work order value by sector",
        "expected_sql_pattern": ['SELECT "Sector", SUM("Amount in Rupees', 'GROUP BY "Sector"'],
        "expected_output": "WO amounts by sector (6 sectors)",
        "data_context": "₹211.6M total across 6 sectors",
        "production_metrics": {
            "expected_rows": 6,
            "expected_columns": 2,
            "execution_time_estimate_ms": 8
        }
    },
    {
        "id": "Q8",
        "category": "Work Order",
        "difficulty": "Medium",
        "question": "How many work orders are completed vs ongoing?",
        "expected_sql_pattern": ['WHERE "Execution Status" IN (\'Completed\', \'Ongoing\')', 'GROUP BY "Execution Status"'],
        "expected_output": "Comparison of completed vs ongoing",
        "data_context": "Status filtering required",
        "production_metrics": {
            "expected_rows": 2,
            "expected_columns": 2,
            "execution_time_estimate_ms": 7
        }
    },
    {
        "id": "Q9",
        "category": "Work Order",
        "difficulty": "Hard",
        "question": "Billing vs collection analysis: how much is billed but not collected?",
        "expected_sql_pattern": ['"Billing Status"', '"Billed Value"', '"Collected Amount"'],
        "expected_output": "AR breakdown showing billed vs collected gap",
        "data_context": "Multiple financial columns, may need COALESCE",
        "production_metrics": {
            "expected_rows": "~5-10",
            "expected_columns": "~3-4",
            "execution_time_estimate_ms": 15
        }
    },
    {
        "id": "Q10",
        "category": "Work Order",
        "difficulty": "Hard",
        "question": "Work orders by nature of work with their execution and billing status",
        "expected_sql_pattern": ['"Nature of Work"', '"Execution Status"', '"Billing Status"', 'COUNT(*)'],
        "expected_output": "Cross-tab: nature x execution x billing",
        "data_context": "3-dimensional grouping, multiple factors",
        "production_metrics": {
            "expected_rows": "~20-30",
            "expected_columns": 4,
            "execution_time_estimate_ms": 18
        }
    },
    
    # ========================================================================
    # GROUP C: DEAL-TO-WORK ORDER JOINS (5 questions)
    # ========================================================================
    {
        "id": "Q11",
        "category": "Deal-WO Join Analysis",
        "difficulty": "Hard",
        "question": "Which deals have work orders and what's the value difference?",
        "expected_sql_pattern": [
            'LEFT JOIN work_orders',
            'ON d."Deal Name" = wo."Deal name masked"',
            'COUNT(wo.'
        ],
        "expected_output": "Deals with WO count and value comparison",
        "data_context": "Join key: Deal Name ↔ Deal name masked",
        "production_metrics": {
            "expected_rows": "~50-100",
            "expected_columns": "~4-5",
            "execution_time_estimate_ms": 25
        }
    },
    {
        "id": "Q12",
        "category": "Deal-WO Join Analysis",
        "difficulty": "Hard",
        "question": "Deals by sector: pipeline value vs work order value (completed projects)",
        "expected_sql_pattern": [
            'LEFT JOIN',
            '"Execution Status" = \'Completed\'',
            'GROUP BY d."Sector/service"'
        ],
        "expected_output": "Sector-level deal vs executed WO comparison",
        "data_context": "Filtered join with aggregation",
        "production_metrics": {
            "expected_rows": "~12",
            "expected_columns": "~3-4",
            "execution_time_estimate_ms": 30
        }
    },
    {
        "id": "Q13",
        "category": "Deal-WO Join Analysis",
        "difficulty": "Very Hard",
        "question": "Deal-to-revenue funnel: from deal to billed to collected (by sector)",
        "expected_sql_pattern": [
            'LEFT JOIN work_orders',
            'COALESCE(d."Masked Deal value", 0) as pipeline_value',
            'COALESCE(billed, 0) as billed_value',
            'COALESCE(collected, 0) as collected_value'
        ],
        "expected_output": "3-stage funnel by sector showing conversion",
        "data_context": "Complex multi-table join with arithmetic",
        "production_metrics": {
            "expected_rows": "~12",
            "expected_columns": "~5-6",
            "execution_time_estimate_ms": 40
        }
    },
    {
        "id": "Q14",
        "category": "Deal-WO Join Analysis",
        "difficulty": "Very Hard",
        "question": "Top 10 deals: show pipeline value, WO status, and billing status",
        "expected_sql_pattern": [
            'LEFT JOIN work_orders',
            'ORDER BY d."Masked Deal value" DESC',
            'LIMIT 10'
        ],
        "expected_output": "Top deals with full deal+WO status",
        "data_context": "Ranking query with join and aggregation",
        "production_metrics": {
            "expected_rows": 10,
            "expected_columns": "~6-8",
            "execution_time_estimate_ms": 35
        }
    },
    {
        "id": "Q15",
        "category": "Deal-WO Join Analysis",
        "difficulty": "Hard",
        "question": "Deals without work orders: what's the value at risk?",
        "expected_sql_pattern": [
            'LEFT JOIN work_orders',
            'WHERE wo."Deal name masked" IS NULL',
            'SUM(d."Masked Deal value")'
        ],
        "expected_output": "Deals with no corresponding WO and their total value",
        "data_context": "Anti-join pattern, NULL filtering",
        "production_metrics": {
            "expected_rows": "~50-80",
            "expected_columns": "~3-4",
            "execution_time_estimate_ms": 20
        }
    }
]

# Additional edge case / advanced questions
ADVANCED_QUESTIONS = [
    {
        "id": "Q16",
        "category": "Advanced Analytics",
        "difficulty": "Very Hard",
        "question": "Q1 2026: pipeline forecast (deals with close dates) vs actual execution (completed WOs)",
        "expected_sql_pattern": [
            'CAST("Tentative Close Date" AS DATE) BETWEEN',
            '"Execution Status" = \'Completed\''
        ],
        "expected_output": "Forecast vs reality comparison",
        "data_context": "Date range + join + filtering",
        "production_metrics": {
            "expected_rows": "~10-20",
            "expected_columns": "~4-5",
            "execution_time_estimate_ms": 35
        }
    },
    {
        "id": "Q17",
        "category": "Advanced Analytics",
        "difficulty": "Very Hard",
        "question": "Sector performance: close rate (Won deals / Total deals) and revenue per owner",
        "expected_sql_pattern": [
            'COUNT(CASE WHEN "Deal Status" = \'Won\')',
            'COUNT(*) as total',
            'GROUP BY "Sector/service", "Owner code"'
        ],
        "expected_output": "Sector+owner matrix with win rates and metrics",
        "data_context": "Conditional aggregation, multi-level grouping",
        "production_metrics": {
            "expected_rows": "~40-60",
            "expected_columns": "~5-6",
            "execution_time_estimate_ms": 40
        }
    },
    {
        "id": "Q18",
        "category": "Advanced Analytics",
        "difficulty": "Very Hard",
        "question": "Deal lifecycle: average days from created to won/closed, by sector",
        "expected_sql_pattern": [
            'EXTRACT(DAY FROM',
            'CAST("Close Date (A)" AS DATE) - CAST("Created Date" AS DATE)',
            'WHERE "Deal Status" = \'Won\''
        ],
        "expected_output": "Average deal cycle time by sector",
        "data_context": "Date arithmetic, conditional filtering",
        "production_metrics": {
            "expected_rows": "~10-12",
            "expected_columns": "~3-4",
            "execution_time_estimate_ms": 25
        }
    }
]

PERFORMANCE_BENCHMARKS = {
    "target_all_queries": "<500ms",
    "target_simple_queries": "<100ms",
    "target_complex_joins": "<100ms",
    "max_acceptable": "2000ms",
    "n_performance_test_runs": 10
}

SUCCESS_CRITERIA = {
    "minimum_questions_passing": 12,  # 80%
    "average_execution_time": "< 50ms",
    "error_rate": "< 5%",
    "insight_quality": "CEO-ready (headline + metrics + analysis)",
    "insight_accuracy": "100% factually correct",
}

if __name__ == "__main__":
    print("FounderBI Agent Test Plan")
    print("=" * 80)
    print(f"\nCore Test Questions: {len(TEST_QUESTIONS)}")
    print(f"Advanced Questions: {len(ADVANCED_QUESTIONS)}")
    print(f"Total Questions: {len(TEST_QUESTIONS) + len(ADVANCED_QUESTIONS)}")
    
    print("\n" + "=" * 80)
    print("QUESTION BREAKDOWN BY CATEGORY")
    print("=" * 80)
    
    categories = {}
    for q in TEST_QUESTIONS:
        cat = q['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} questions")
    
    print("\nSuccess Criteria:")
    for criterion, value in SUCCESS_CRITERIA.items():
        print(f"  • {criterion}: {value}")
