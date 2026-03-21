import os
import requests
from dotenv import load_dotenv

load_dotenv()

def run():
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    urls = [
        "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1/v1/chat/completions",
        "https://router.huggingface.co/models/deepseek-ai/DeepSeek-R1/v1/chat/completions",
        "https://router.huggingface.co/v1/chat/completions",
        "https://router.huggingface.co/hf-inference/models/deepseek-ai/DeepSeek-R1/v1/chat/completions",
        "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-Coder-V2-Instruct/v1/chat/completions",
        "https://api-inference.huggingface.co/v1/chat/completions"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    
    for url in urls:
        print(f"\nTesting: {url}")
        resp = requests.post(url, headers=headers, json=payload)
        print("Status:", resp.status_code)
        if resp.status_code == 200:
            print("SUCCESS")
            break
        else:
            try:
                print("Response:", resp.json())
            except:
                print("Text:", resp.text)

if __name__ == "__main__":
    run()
