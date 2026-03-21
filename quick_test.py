#!/usr/bin/env python3
"""Quick test of founder questions - simplified output"""
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/query"

questions = [
    "What's our total pipeline value by sector?",
    "Who are our top 3 performing deal owners?",
    "What's our overall deal-to-work-order conversion rate?",
    "How much work order value is at-risk due to delays?",
    "Which deals will close in the next 30 days?",
    "What's our overall collection rate?",
]

print("\n" + "="*80)
print("FOUNDER BI AGENT - QUICK TEST (6 Questions)")
print("="*80 + "\n")

results = []
for i, q in enumerate(questions, 1):
    print(f"Q{i}: {q}")
    
    try:
        start = time.time()
        r = requests.post(API_URL, json={"question": q, "conversation_history": []}, timeout=120)
        elapsed = time.time() - start
        
        if r.status_code == 200:
            data = r.json()
            has_answer = bool(data.get("answer"))
            has_sql = bool(data.get("sql_query"))
            has_data = len(data.get("result_records", [])) > 0
            
            if has_answer and not data.get("needs_clarification"):
                print(f"  ✅ SUCCESS ({elapsed:.1f}s)")
                print(f"     Answer: {data['answer'][:120]}...")
                results.append(("SUCCESS", elapsed))
            else:
                status = "CLARIFY" if data.get("needs_clarification") else "NO_ANSWER"
                print(f"  ⚠️  {status} ({elapsed:.1f}s)")
                results.append((status, elapsed))
        else:
            print(f"  ❌ HTTP {r.status_code}")
            results.append(("ERROR", 0))
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)[:60]}")
        results.append(("ERROR", 0))
    
    print()

# Summary
print("="*80)
print("SUMMARY")
print("="*80)
success_count = sum(1 for s, _ in results if s == "SUCCESS")
print(f"Results: {success_count}/{len(questions)} successful")
print(f"Avg Time: {sum(t for _, t in results if t > 0) / len([t for _, t in results if t > 0]):.1f}s")
for i, (status, elapsed) in enumerate(results, 1):
    print(f"  Q{i}: {status} ({elapsed:.1f}s)")
print("="*80 + "\n")
