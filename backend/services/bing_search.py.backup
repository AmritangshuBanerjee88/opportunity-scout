"""
Bing Search API service for finding speaking opportunities.
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BingSearchService:
    """
    Service for searching the web using Bing Search API.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the Bing Search service.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get API key from environment
        self.api_key = os.getenv("BING_SEARCH_API_KEY")
        if not self.api_key:
            raise ValueError("BING_SEARCH_API_KEY environment variable not set")
        
        # Set up endpoint and parameters
        self.endpoint = self.config['bing_search']['endpoint']
        self.results_per_query = self.config['bing_search']['results_per_query']
        self.market = self.config['bing_search']['market']
        self.safe_search = self.config['bing_search']['safe_search']
        
        # Get search query templates
        self.query_templates = self.config['search']['search_query_templates']
    
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
    
    def _execute_search(self, query: str) -> Dict[str, Any]:
        """
        Execute a single Bing search query.
        
        Args:
            query: Search query string
        
        Returns:
            Search results dictionary
        """
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        
        params = {
            "q": query,
            "count": self.results_per_query,
            "mkt": self.market,
            "safeSearch": self.safe_search,
            "textFormat": "HTML",
            "freshness": "Month"  # Focus on recent results
        }
        
        try:
            response = requests.get(
                self.endpoint,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Bing search error for query '{query}': {str(e)}")
            return {"webPages": {"value": []}}
    
    def _format_results(self, raw_results: List[Dict[str, Any]]) -> str:
        """
        Format raw Bing results into a text format for AI processing.
        
        Args:
            raw_results: List of raw search result dictionaries
        
        Returns:
            Formatted string of search results
        """
        formatted = []
        seen_urls = set()
        
        for result in raw_results:
            web_pages = result.get("webPages", {}).get("value", [])
            
            for page in web_pages:
                url = page.get("url", "")
                
                # Skip duplicate URLs
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                title = page.get("name", "No title")
                snippet = page.get("snippet", "No description")
                
                # Clean up HTML from snippet
                snippet = snippet.replace("<b>", "").replace("</b>", "")
                
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
        logger.info(f"Starting search with keywords: {keywords}")
        
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
        
        logger.info(f"Search complete. Found results from {len(all_results)} queries")
        
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