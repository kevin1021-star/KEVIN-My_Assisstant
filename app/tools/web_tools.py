import os
import importlib

def get_web_browsing_tool():
    """Return an optional Tavily tool when the dependency and key are available."""
    if not os.environ.get("TAVILY_API_KEY"):
        return None

    try:
        tavily_module = importlib.import_module("langchain_community.tools.tavily_search")
        return tavily_module.TavilySearchResults(max_results=3)
    except Exception:
        return None
