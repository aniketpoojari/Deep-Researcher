"""Web search tool definition for LangChain/LangGraph integration."""

from typing import Dict
from langchain_core.tools import tool
from utils.websearch import WebSearch
from logger.logging import get_logger

logger = get_logger(__name__)


class WebSearchTool:
    """
    LangChain tool wrapper for web search.

    Provides a search_web tool that can be used with LangGraph agents.
    """

    def __init__(self):
        self._client = WebSearch()
        self.tools = [self._create_search_tool()]
        logger.info("WebSearchTool initialized")

    def _create_search_tool(self):
        """Create the search_web tool."""

        @tool
        def search_web(query: str, max_results: int = 3) -> Dict:
            """
            Search the web for information.

            Args:
                query: The search query
                max_results: Maximum number of results (default: 3)

            Returns:
                Dict with success status and results list
            """
            try:
                results = self._client.search(query, max_results)
                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results),
                }
            except Exception as e:
                logger.error(f"search_web failed: {e}")
                return {
                    "success": False,
                    "query": query,
                    "error": str(e),
                }

        return search_web
