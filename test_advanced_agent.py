import os
from dotenv import load_dotenv
from founder_bi_agent.backend.service import FounderBIService

load_dotenv(override=True)

def test():
    print(f"HUGGINGFACE: {'set' if os.getenv('HUGGINGFACE_API_KEY') else 'not set'}")
    print(f"TAVILY: {'set' if os.getenv('TAVILY_API_KEY') else 'not set'}")
    print(f"PROVIDER: {os.getenv('LLM_PROVIDER')}")
    
    svc = FounderBIService()
    os.environ["LLM_PROVIDER"] = "huggingface"
    svc.settings.llm_provider = "huggingface"
    
    question = "What is the total pipeline value of deals in the Retail sector, and based on current market trends via web search, is this sector growing globally?"
    print(f"\nQuestion: {question}\n")
    
    result = svc.run_query(question)
    
    print("\n====================")
    print("FINAL ANSWER:")
    print("====================")
    print(result.get("answer"))
    
    print("\n====================")
    print("TRACES (DeepSeek & Tavily):")
    print("====================")
    for t in result.get("traces", []):
        print(f"\n[{t['node']}]")
        details = t.get('details', {})
        for k, v in details.items():
            # truncate long strings for readability
            v_str = str(v)
            if len(v_str) > 300:
                v_str = v_str[:300] + "..."
            print(f"  {k}: {v_str}")

if __name__ == "__main__":
    test()
