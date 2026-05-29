"""Simple web search tool (mock for now)."""
from typing import Any, Dict, List


def web_search(query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    Search the web (mocked for now).

    In reality, would use real search API.
    For learning, returns mock results.

    Args:
        query: Search query
        num_results: Number of results

    Returns:
        Dict with results
    """
    mock_results: List[Dict] = [
        {
            "title": f"Result for: {query}",
            "url": f"https://example.com/search?q={query.replace(' ', '+')}",
            "snippet": f"This is a mock search result for '{query}'",
        }
    ] * num_results

    return {
        "success": True,
        "query": query,
        "num_results": num_results,
        "results": mock_results,
    }


WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information. Use when you need real-time data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (1-10)",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
}


if __name__ == "__main__":
    print(web_search("latest AI news"))
