import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tavily import TavilyClient
from config.settings import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


def search_facts(query: str) -> str:
    try:
        if not client:
            print("Warning: Tavily client is not initialized (TAVILY_API_KEY not set).")
            return ""

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=True,
        )

        if response.get("answer"):
            return response["answer"]

        results = response.get("results", [])
        snippets = [r.get("content", "") for r in results[:2] if r.get("content")]
        return " ".join(snippets)
    except Exception as e:
        print(f"Warning: Tavily search failed: {e}")
        return ""


if __name__ == "__main__":
    print(search_facts("travel distance and time from Nagpur to Delhi by train"))
