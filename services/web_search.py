import os
import logging
from tavily import TavilyClient
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Check if API key is configured
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

class WebSearchService:
    """Service for performing web searches using Tavily API"""
    
    def __init__(self):
        self.client = None
        if TAVILY_API_KEY and TAVILY_API_KEY != "your_tavily_api_key_here":
            try:
                self.client = TavilyClient(api_key=TAVILY_API_KEY)
                logger.info("Tavily client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
                self.client = None
        else:
            logger.warning("TAVILY_API_KEY not configured or using placeholder")
    
    def is_available(self) -> bool:
        """Check if web search service is available"""
        return self.client is not None
    
    def search_web(self, query: str, max_results: int = 3) -> Optional[List[Dict]]:
        """
        Perform a web search using Tavily API
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results or None if search failed
        """
        if not self.is_available():
            logger.warning("Web search service not available - TAVILY_API_KEY not configured")
            return None
        
        try:
            # Perform the search
            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer=True,
                include_images=False
            )
            
            # Extract relevant information from response
            results = []
            if response and 'results' in response:
                for result in response['results']:
                    results.append({
                        'title': result.get('title', 'No title'),
                        'url': result.get('url', ''),
                        'content': result.get('content', 'No content'),
                        'score': result.get('score', 0)
                    })
            
            logger.info(f"Web search completed for query: '{query}' - Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {e}")
            return None
    
    def get_latest_news(self, topic: str = "technology", max_results: int = 5) -> Optional[List[Dict]]:
        """
        Get latest news on a specific topic
        
        Args:
            topic: News topic (e.g., "technology", "sports", "politics")
            max_results: Maximum number of news items to return
            
        Returns:
            List of news items or None if search failed
        """
        query = f"latest news about {topic}"
        return self.search_web(query, max_results)
    
    def get_weather_info(self, location: str) -> Optional[List[Dict]]:
        """
        Get weather information for a specific location
        
        Args:
            location: City name or location
            
        Returns:
            Weather information or None if search failed
        """
        query = f"current weather in {location}"
        return self.search_web(query, 1)

# Global instance
web_search_service = WebSearchService()

def perform_web_search(query: str, max_results: int = 3) -> Optional[List[Dict]]:
    """Convenience function to perform web search"""
    return web_search_service.search_web(query, max_results)

def get_news(topic: str = "technology", max_results: int = 5) -> Optional[List[Dict]]:
    """Convenience function to get latest news"""
    return web_search_service.get_latest_news(topic, max_results)

def get_weather(location: str) -> Optional[List[Dict]]:
    """Convenience function to get weather information"""
    return web_search_service.get_weather_info(location)
