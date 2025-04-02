from duckduckgo_search import DDGS

def web_search(max_results: int = 10, **kwargs) -> str:
    """
    Performs a DuckDuckGo web search based on your query (think a Google search) then returns the top search results.

    Args:
        query (str): The search query to perform.
        max_results (int, optional): Maximum number of results to return. Defaults to 10.
        **kwargs: Additional keyword arguments to pass to DDGS.

    Returns:
        str: Formatted string containing search results.

    Raises:
        ImportError: If the duckduckgo_search package is not installed.
        Exception: If no results are found for the given query.
    """
    try:
        ddgs = DDGS()
    except ImportError as e:
        raise ImportError("You must install package `duckduckgo_search` to run this function: for instance run `pip install duckduckgo-search`."
        ) from e
    query = kwargs['query']
    results = ddgs.text(query, max_results=max_results)
    if len(results) == 0:
        raise Exception("No results found! Try a less restrictive/shorter query.")

    postprocessed_results = [f"[{result['title']}]({result['href']})\n{result['body']}" for result in results]
    return "## Search Results\n\n" + "\n\n".join(postprocessed_results)