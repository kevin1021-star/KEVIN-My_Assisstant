from langchain_community.tools.tavily_search import TavilySearchResults
import os

# Create the standard web browsing tool using Tavily
def get_web_browsing_tool():
    """Returns a configured Tavily search tool that LangChain can use to surf the live internet."""
    # Tavily automatically looks for TAVILY_API_KEY inside the env
    search = TavilySearchResults(max_results=3)
    return search
