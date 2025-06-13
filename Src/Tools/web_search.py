import os
from dotenv import load_dotenv
from duckduckgo_search import DDGS
import requests

load_dotenv()

def web_search(max_results: int = 10, **kwargs) -> str:
    """
    Performs a DuckDuckGo web search based on your query (think a Google search) then returns the top search results.
    Falls back to SerpAPI (Google) if DuckDuckGo fails or returns no results.

    Args:
        query (str): The search query to perform.
        max_results (int, optional): Maximum number of results to return. Defaults to 10.
        **kwargs: Additional keyword arguments to pass to DDGS.

    Returns:
        str: Formatted string containing search results.

    Raises:
        ImportError: If neither duckduckgo_search nor SerpAPI is available.
        Exception: If no results are found for the given query.
    """
    query = kwargs['query']
    # Try DuckDuckGo first
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=max_results)
        if results and len(results) > 0:
            postprocessed_results = [f"[{result['title']}]({result['href']})\n{result['body']}" for result in results]          
            return "## Search Results (DuckDuckGo)\n\n" + "\n\n".join(postprocessed_results)
    except Exception:
        pass  # Will try SerpAPI fallback

    # Fallback to SerpAPI (Google)
    SERP_API_KEY = os.getenv("SERP_API_KEY")
    if not SERP_API_KEY:
        raise ImportError("DuckDuckGo search failed and SERP_API_KEY is not set for SerpAPI fallback.")
    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google"
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        results = data.get("organic_results", [])
        if not results:
            raise Exception("No results found from SerpAPI either!")
        simplified_results = [
            f"[{result.get('title')}]({result.get('link')})\n{result.get('snippet', '')}"
            for result in results[:max_results]
        ]
        return "## Search Results (Google via SerpAPI)\n\n" + "\n\n".join(simplified_results)
    except Exception as e:
        raise Exception(f"No results found from DuckDuckGo or SerpAPI. Last error: {e}")