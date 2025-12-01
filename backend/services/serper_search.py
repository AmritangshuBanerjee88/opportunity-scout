"""
Serper.dev Google Search API service for finding speaking opportunities.
Replaces Bing Search with Google Search via Serper.
"""

import os
import requests
import logging
from typing import List, Dict, Any
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SerperSearchService:
    """
    Service for searching the web using Serper.dev Google Search API.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the Serper Search service.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get API key from environment
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY environment variable not set")
        
        # Serper endpoint
        self.endpoint = "https://google.serper.dev/search"
        
        # Get search query templates
        self.query_templates = self.config.get('search', {}).get('search_query_templates', [
            "{keyword} conference call for speakers 2025",
            "{keyword} summit speaker application",
            "{keyword} webinar guest speaker opportunity"
        ])
    
    def _build_queries(self, keywords: List[str], opportunity_types: List[str]) -> List[str]:
        """
        Build search queries from keywords and opportunity types.
        
        Args:
            keywords: List of search keywords
            opportunity_types: Types of opportunities to search for
        
        Returns:
            List of search query strings
        """
        queries = []
        
        for keyword in keywords:
            # Use templates from config
            for template in self.query_templates:
                query = template.format(keyword=keyword)
                queries.append(query)
            
            # Add opportunity type specific queries
            for opp_type in opportunity_types:
                queries.append(f"{keyword} {opp_type} speaker opportunity 2025")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)
        
        return unique_queries
    
    def _execute_search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """
        Execute a single Serper search query.
        
        Args:
            query: Search query string
            num_results: Number of results to return
        
        Returns:
            Search results dictionary
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results
        }
        
        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper search error for query '{query}': {str(e)}")
            return {"organic": []}
    
    def _format_results(self, raw_results: List[Dict[str, Any]]) -> str:
        """
        Format raw Serper results into a text format for AI processing.
        
        Args:
            raw_results: List of raw search result dictionaries
        
        Returns:
            Formatted string of search results
        """
        formatted = []
        seen_urls = set()
        
        for result in raw_results:
            organic = result.get("organic", [])
            
            for item in organic:
                url = item.get("link", "")
                
                # Skip duplicate URLs
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                title = item.get("title", "No title")
                snippet = item.get("snippet", "No description")
                
                formatted.append(f"""
---
Title: {title}
URL: {url}
Description: {snippet}
---""")
        
        return "\n".join(formatted)
    
    def search(
        self,
        keywords: List[str],
        opportunity_types: List[str],
        max_queries: int = 5
    ) -> str:
        """
        Search for speaking opportunities.
        
        Args:
            keywords: List of search keywords
            opportunity_types: Types of opportunities to search for
            max_queries: Maximum number of queries to execute
        
        Returns:
            Formatted string of all search results
        """
        logger.info(f"Starting Serper search with keywords: {keywords}")
        
        # Build search queries
        queries = self._build_queries(keywords, opportunity_types)
        
        # Limit number of queries
        queries = queries[:max_queries]
        logger.info(f"Executing {len(queries)} search queries")
        
        # Execute searches
        all_results = []
        for query in queries:
            logger.info(f"Searching: {query}")
            results = self._execute_search(query)
            all_results.append(results)
        
        # Format results for AI processing
        formatted_results = self._format_results(all_results)
        
        result_count = sum(len(r.get("organic", [])) for r in all_results)
        logger.info(f"Search complete. Found {result_count} total results")
        
        return formatted_results
    
    def get_raw_results(
        self,
        keywords: List[str],
        opportunity_types: List[str],
        max_queries: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get raw search results (for debugging or additional processing).
        
        Args:
            keywords: List of search keywords
            opportunity_types: Types of opportunities to search for
            max_queries: Maximum number of queries to execute
        
        Returns:
            List of raw result dictionaries
        """
        queries = self._build_queries(keywords, opportunity_types)[:max_queries]
        
        all_results = []
        for query in queries:
            results = self._execute_search(query)
            all_results.append({
                "query": query,
                "results": results
            })
        
        return all_results


# Backward compatibility alias
BingSearchService = SerperSearchService
