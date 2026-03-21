#!/usr/bin/env python3
"""
Founder BI Agent - Production Verification Test Suite
Tests 5-6 founder-level business intelligence questions against real Monday.com data
"""

import requests
import json
import time
import sys
from datetime import datetime

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

API_URL = "http://127.0.0.1:8000/query"
HEADERS = {"Content-Type": "application/json"}

# Founder-level questions based on real dataset
FOUNDER_QUESTIONS = [
    {
        "id": 1,
        "question": "What's our total pipeline value and how is it distributed by sector?",
        "category": "Strategic Pipeline Analysis",
        "expected_metrics": ["total_value", "sector_breakdown", "energy", "renewables", "mining"]
    },
    {
        "id": 2,
        "question": "Which deal owners are performing best by pipeline value and how much concentration risk do we have?",
        "category": "Team Performance & Risk",
        "expected_metrics": ["owner_performance", "top_3_owners", "concentration", "risk_level"]
    },
    {
        "id": 3,
        "question": "What's our deal-to-work-order conversion rate by sector and where are we winning vs losing?",
        "category": "Conversion Analysis",
        "expected_metrics": ["conversion_rate", "sector_performance", "bottlenecks"]
    },
    {
        "id": 4,
        "question": "How much work order value is at risk due to execution delays or billing issues?",
        "category": "Cash Flow & Risk",
        "expected_metrics": ["at_risk_amount", "billing_status", "execution_health"]
    },
    {
        "id": 5,
        "question": "Which deals are closest to closing in the next 30 days and what's the revenue impact?",
        "category": "Short-term Revenue Forecast",
        "expected_metrics": ["near_term_deals", "expected_revenue", "close_probability"]
    },
    {
        "id": 6,
        "question": "What's our collection rate vs billed value and how much cash are we actually receiving?",
        "category": "Financial Reality Check",
        "expected_metrics": ["collection_rate", "collection_efficiency", "receivables"]
    },
]

def print_header():
    """Print test suite header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 100)
    print("  FOUNDER BI AGENT - PRODUCTION VERIFICATION TEST SUITE")
    print("  Testing 6 Founder-Level Questions Against Real Monday.com Data")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    print(f"{Colors.ENDC}\n")

def print_question(question_obj):
    """Print question header"""
    print(f"{Colors.CYAN}{Colors.BOLD}Q{question_obj['id']}: {question_obj['question']}{Colors.ENDC}")
    print(f"    Category: {Colors.BLUE}{question_obj['category']}{Colors.ENDC}")
    print(f"    Expected: {Colors.YELLOW}{', '.join(question_obj['expected_metrics'][:3])}...{Colors.ENDC}\n")

def check_response_health(response_data, question_obj):
    """Validate response structure and quality"""
    issues = []
    
    # Check basic structure
    if not response_data.get("answer"):
        issues.append("❌ NO ANSWER PROVIDED")
    if response_data.get("needs_clarification"):
        issues.append("⚠️ NEEDS CLARIFICATION (shouldn't be needed with specific question)")
    
    # Check metadata
    if not response_data.get("sql_query"):
        issues.append("⚠️ NO SQL QUERY GENERATED")
    if response_data.get("sql_validation_error"):
        issues.append(f"⚠️ SQL VALIDATION ERROR: {response_data['sql_validation_error']}")
    
    # Check results
    result_count = len(response_data.get("result_records", []))
    if result_count == 0:
        issues.append("⚠️ NO DATA RETURNED")
    elif result_count > 1000:
        issues.append(f"⚠️ TOO MANY RESULTS: {result_count} rows")
    
    # Check traces
    trace_count = len(response_data.get("traces", []))
    if trace_count < 3:  # Should have multiple trace steps
        issues.append(f"⚠️ FEW TRACE STEPS: {trace_count}")
    
    return issues

def print_response(response_data, question_obj):
    """Print formatted response"""
    
    # Health check
    issues = check_response_health(response_data, question_obj)
    
    if response_data.get("needs_clarification"):
        print(f"{Colors.YELLOW}❓ CLARIFICATION NEEDED:{Colors.ENDC}")
        print(f"   {response_data.get('clarification_question', 'No clarification question')}\n")
        return False  # Shouldn't need clarification for specific question
    
    # Answer
    answer = response_data.get("answer", "")
    if answer:
        print(f"{Colors.GREEN}{Colors.BOLD}EXECUTIVE INSIGHT:{Colors.ENDC}")
        print(f"{answer}\n")
    
    # SQL Query
    sql = response_data.get("sql_query", "")
    if sql:
        print(f"{Colors.BLUE}Generated SQL:{Colors.ENDC}")
        # Make SQL readable
        sql_pretty = sql.replace(" WHERE ", "\n    WHERE ").replace(" GROUP BY ", "\n    GROUP BY ").replace(" ORDER BY ", "\n    ORDER BY ")
        print(f"  {sql_pretty[:200]}..." if len(sql_pretty) > 200 else f"  {sql_pretty}")
        print()
    
    # Data Sample
    records = response_data.get("result_records", [])
    if records:
        print(f"{Colors.BLUE}Data Sample ({len(records)} rows):{Colors.ENDC}")
        for i, record in enumerate(records[:3], 1):
            print(f"  {i}. {record}")
        if len(records) > 3:
            print(f"  ... and {len(records) - 3} more rows")
        print()
    
    # Health Status
    print(f"{Colors.BOLD}Health Check:{Colors.ENDC}")
    if not issues:
        print(f"  {Colors.GREEN}✅ ALL CHECKS PASSED{Colors.ENDC}")
    else:
        for issue in issues:
            print(f"  {issue}")
    print("\n")
    
    return len(issues) == 0

def test_api_connectivity():
    """Test if API is responding"""
    try:
        response = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ Backend API is UP and responding{Colors.ENDC}\n")
            return True
    except Exception as e:
        print(f"{Colors.RED}❌ Backend API NOT RESPONDING: {e}{Colors.ENDC}\n")
        return False

def run_test(question_obj):
    """Run single test question"""
    print_question(question_obj)
    
    payload = {
        "question": question_obj["question"],
        "conversation_history": []
    }
    
    try:
        start_time = time.time()
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=60)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            success = print_response(data, question_obj)
            
            # Timing
            print(f"{Colors.BOLD}Performance:{Colors.ENDC}")
            print(f"  Response Time: {Colors.GREEN}{elapsed:.2f}s{Colors.ENDC}")
            print(f"  Trace Steps: {len(data.get('traces', []))}")
            print(f"  {Colors.BOLD}{'─' * 90}{Colors.ENDC}\n")
            
            return {
                "success": success,
                "elapsed": elapsed,
                "records": len(data.get("result_records", [])),
                "status_code": 200
            }
        else:
            print(f"{Colors.RED}❌ HTTP Error {response.status_code}{Colors.ENDC}")
            print(f"   Response: {response.text[:200]}\n")
            return {
                "success": False,
                "elapsed": elapsed,
                "status_code": response.status_code
            }
            
    except Exception as e:
        print(f"{Colors.RED}❌ ERROR: {str(e)}{Colors.ENDC}\n")
        return {
            "success": False,
            "error": str(e)
        }

def print_summary(results):
    """Print test summary"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("=" * 100)
    print("  TEST SUMMARY")
    print("=" * 100)
    print(f"{Colors.ENDC}\n")
    
    total = len(results)
    successful = sum(1 for r in results if r.get("success"))
    avg_time = sum(r.get("elapsed", 0) for r in results) / total if total > 0 else 0
    total_records = sum(r.get("records", 0) for r in results)
    
    print(f"  Total Tests: {total}")
    print(f"  ✅ Successful: {Colors.GREEN}{successful}{Colors.ENDC} / {total}")
    print(f"  ❌ Failed: {Colors.RED}{total - successful}{Colors.ENDC} / {total}")
    print(f"  Average Response Time: {Colors.YELLOW}{avg_time:.2f}s{Colors.ENDC}")
    print(f"  Total Records Retrieved: {total_records}")
    print(f"  Success Rate: {Colors.GREEN if successful == total else Colors.YELLOW}{(successful/total)*100:.1f}%{Colors.ENDC}\n")
    
    # Individual results
    print(f"{Colors.BOLD}Question Results:{Colors.ENDC}")
    for i, result in enumerate(results, 1):
        status = f"{Colors.GREEN}✅{Colors.ENDC}" if result.get("success") else f"{Colors.RED}❌{Colors.ENDC}"
        timing = f"{result.get('elapsed', 0):.2f}s" if result.get("elapsed") else "ERROR"
        print(f"  Q{i}: {status} ({timing})")
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 100}{Colors.ENDC}\n")
    
    if successful == total:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED - System is Production Ready!{Colors.ENDC}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ Some tests had issues - Review above for details{Colors.ENDC}\n")
        return 1

def main():
    print_header()
    
    # Test connectivity
    if not test_api_connectivity():
        print(f"{Colors.RED}Cannot proceed without API connectivity{Colors.ENDC}")
        return 1
    
    # Run tests
    results = []
    for question_obj in FOUNDER_QUESTIONS:
        result = run_test(question_obj)
        results.append(result)
        time.sleep(0.5)  # Small delay between requests
    
    # Print summary
    exit_code = print_summary(results)
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
