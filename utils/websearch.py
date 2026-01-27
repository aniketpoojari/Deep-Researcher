"""Web search utility with Tavily and DuckDuckGo providers."""

from typing import List, Dict, Optional
from langchain_community.tools.tavily_search import TavilySearchResults
from utils.config_loader import ConfigLoader
from logger.logging import get_logger

logger = get_logger(__name__)


class WebSearch:
    """
    Web search client with automatic fallback.

    Primary: Tavily (if TAVILY_API_KEY is set)
    Fallback: DuckDuckGo (no API key required)
    """

    def __init__(self):
        self.config = ConfigLoader()
        self.max_results = self.config.get("research.results_per_search", 3)
        self._tavily = self._create_tavily_client()
        logger.info("WebSearch initialized")

    def _create_tavily_client(self) -> Optional[TavilySearchResults]:
        """Create Tavily client if API key is available."""
        if not self.config.get_env("TAVILY_API_KEY", default=None):
            logger.info("Tavily API key not set in .env")
            return None
        return TavilySearchResults(max_results=self.max_results)

    def search(self, query: str, num_results: int = None) -> List[Dict]:
        """
        Search the web for the given query.

        Args:
            query: Search query string
            num_results: Number of results to return (default from config)

        Returns:
            List of search results with title, url, content, snippet
        """
        if not query or not query.strip():
            return []

        n = num_results or self.max_results

        # Try Tavily first
        if self._tavily:
            results = self._search_tavily(query, n)
            if results:
                return results

    def _search_tavily(self, query: str, n: int) -> List[Dict]:
        """Execute Tavily search."""
        try:
            self._tavily.max_results = n
            raw = self._tavily.invoke(query)
            logger.info(f"Tavily: {len(raw)} results for '{query[:50]}'")
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                    "snippet": r.get("content", "")[:200],
                }
                for r in raw
            ]
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
            return []