import requests
from typing import Any
from founder_bi_agent.backend.core.config import AgentSettings

class WebResearchTools:
    def __init__(self, settings: AgentSettings):
        self.api_key = settings.tavily_api_key
        self.base_url = "https://api.tavily.com/search"

    def search_market_trends(self, query: str, max_results: int = 3) -> list[dict[str, Any]]:
        """
        Executes an AI-optimized web search using Tavily to retrieve current market trends,
        competitor analysis, or macroeconomic context.
        """
        if not self.api_key:
            return [{"title": "Missing Config", "content": "Tavily API key not configured. Web context skipped.", "url": ""}]
        
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_answer": True
        }
        try:
            resp = requests.post(self.base_url, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            # Prepend the AI answer if available
            if data.get("answer"):
                results.insert(0, {"title": "Tavily Synthesis", "content": data["answer"], "url": "tavily.com"})
            return results
        except requests.exceptions.RequestException as e:
            return [{"title": "Search Error", "content": f"Web search failed: {str(e)}", "url": ""}]
