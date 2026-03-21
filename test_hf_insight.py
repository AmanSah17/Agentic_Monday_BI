import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def run():
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    url = "https://router.huggingface.co/v1/"
    
    client = ChatOpenAI(
        model="deepseek-ai/DeepSeek-R1",
        api_key=api_key,
        base_url=url,
        max_retries=1,
        timeout=120
    )
    try:
        resp = client.invoke("Write a 5 sentence analysis on why Deals by Owner is an important metric. Use markdown.")
        print("CONTENT LENGTH:", len(resp.content))
        print("CONTENT:", resp.content)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    run()
