import logging
import time
from founder_bi_agent.backend.service import run_founder_query

logging.basicConfig(level=logging.WARNING)

questions = [
    "What is the total deal value across all deals currently in our pipeline?",
    "Break down our current open work orders by their status."
]

print("==============================================")
print("🚀 TESTING GROQ END-TO-END PIPELINE")
print("==============================================")

for q in questions:
    print(f"\n[QUERY] {q}")
    start = time.perf_counter()
    try:
        res = run_founder_query(q)
        print(f"[SQL GENERATED]: {res.get('sql_query')}")
        print(f"[RECORDS RETRIEVED]: {len(res.get('result_records', []))}")
        print(f"\n[FINAL LLM INSIGHT]:\n{res.get('answer')}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
    print(f"[TIME TAKEN]: {time.perf_counter() - start:.2f}s")
    print("-" * 60)
