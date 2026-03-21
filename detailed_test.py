#!/usr/bin/env python3
"""Detailed test of founder questions with full responses"""
import sys
import io
import requests
import json
import time

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_URL = "http://127.0.0.1:8000/query"

questions = [
    "What's our total pipeline value by sector?",
    "Who are our top 3 performing deal owners?",
    "What's our overall deal-to-work-order conversion rate?",
    "How much work order value is at-risk due to delays?",
    "Which deals will close in the next 30 days?",
    "What's our overall collection rate?",
]

print("\n" + "="*100)
print("FOUNDER BI AGENT - DETAILED TEST (6 Questions)")
print("="*100 + "\n")

for i, q in enumerate(questions, 1):
    print(f"\n{'='*100}")
    print(f"Q{i}: {q}")
    print('='*100)
    
    try:
        start = time.time()
        r = requests.post(API_URL, json={"question": q, "conversation_history": []}, timeout=120)
        elapsed = time.time() - start
        
        if r.status_code == 200:
            data = r.json()
            
            # Check clarification
            if data.get("needs_clarification"):
                print(f"⚠️  CLARIFICATION NEEDED ({elapsed:.1f}s)")
                print(f"   Question: {data.get('clarification_question')}")
            else:
                print(f"✅ ANSWER READY ({elapsed:.1f}s)")
            
            # Show answer (if any)
            if data.get("answer"):
                answer_preview = data["answer"][:300]
                if len(data["answer"]) > 300:
                    answer_preview += "..."
                print(f"\n   Answer ({len(data['answer'])} chars):")
                print(f"   {answer_preview}")
            
            # Show SQL query if generated
            if data.get("sql_query"):
                print(f"\n   SQL Generated:")
                print(f"   {data['sql_query'][:200]}...")
            
            # Show result count
            if data.get("result_records"):
                print(f"\n   Results: {len(data['result_records'])} rows")
            
            # Show any SQL errors
            if data.get("sql_validation_error"):
                print(f"\n   ❌ SQL Error: {data['sql_validation_error']}")
            
        else:
            print(f"  ❌ HTTP {r.status_code}")
            print(f"  {r.text[:200]}")
    
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")

print("\n" + "="*100 + "\n")
