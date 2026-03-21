from typing import Tuple, Any
from openai import OpenAI
from founder_bi_agent.backend.config import AgentSettings

class HuggingFaceClient:
    """
    Client for interacting with DeepSeek-R1 and similar advanced reasoning models via HuggingFace's 
    OpenAI-compatible Serverless or Dedicated Inference Endpoints.
    """
    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.api_key = settings.huggingface_api_key
        # Default HF Serverless endpoint for v1/chat/completions using router setup
        self.base_url = "https://router.huggingface.co/v1/"
        
        # DeepSeek-R1 target
        self.model_id = "deepseek-ai/DeepSeek-R1" 
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    def refine_plan(self, question: str, history: list[dict[str, str]] = None) -> Tuple[bool, str, str]:
        """
        Act as the Executive Brain.
        Returns: (needs_web_search, search_query, internal_reasoning)
        """
        if not self.client:
            return False, "", "API Key missing."
            
        system_prompt = (
            "You are the Executive Brain for Agentic Monday BI. Overlook the user's CRM query. "
            "Determine if answering this requires external market context (macroeconomics, competitor news, global trends). "
            "Respond in strictly structured format: \n"
            "<think>...your deep reasoning here...</think>\n"
            "<needs_web_search>true/false</needs_web_search>\n"
            "<search_query>best web search query if needed</search_query>"
        )
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": question})

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=1024,
                temperature=0.6,
            )
            content = response.choices[0].message.content or ""
            
            # Simple XML parsing since regex can be brittle here
            think_tag = content.split("</think>")
            reasoning = think_tag[0].replace("<think>", "").strip() if len(think_tag) > 1 else ""
            
            needs_search = "<needs_web_search>true" in content.lower()
            
            search_query = ""
            if "<search_query>" in content and "</search_query>" in content:
                search_query = content.split("<search_query>")[1].split("</search_query>")[0].strip()
                
            return needs_search, search_query, reasoning
        except Exception as e:
            return False, "", f"DeepSeek reasoning error: {str(e)}"
