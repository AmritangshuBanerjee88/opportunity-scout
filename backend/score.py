"""
Azure ML Scoring Script for Opportunity Scout.

This script handles incoming requests to the Azure ML endpoint
and orchestrates the search and extraction process.
"""

import os
import json
import logging
import sys

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.serper_search import SerperSearchService
from services.ai_processor import AIProcessor
from models.opportunity import SearchRequest, SearchResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances (initialized once)
search_service = None
ai_processor = None


def init():
    """
    Initialize the scoring script.
    Called once when the endpoint starts.
    """
    global search_service, ai_processor
    
    logger.info("Initializing Opportunity Scout endpoint...")
    
    try:
        # Initialize services
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config.yaml"
        )
        
        search_service = SerperSearchService(config_path)
        ai_processor = AIProcessor(config_path)
        
        logger.info("Initialization complete!")
        logger.info(f"Model info: {ai_processor.get_model_info()}")
    
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        raise


def run(raw_data: str) -> str:
    """
    Process a search request.
    
    Args:
        raw_data: JSON string with search request
    
    Returns:
        JSON string with search results
    """
    logger.info("Received search request")
    
    try:
        # Parse request
        request_data = json.loads(raw_data)
        search_request = SearchRequest(**request_data)
        
        logger.info(f"Searching for: {search_request.keywords}")
        
        # Step 1: Search with Serper
        search_results = search_service.search(
            keywords=search_request.keywords,
            opportunity_types=search_request.opportunity_types,
            max_queries=min(5, search_request.max_results // 4 + 1)
        )
        
        if not search_results.strip():
            logger.warning("No search results found")
            return json.dumps({
                "search_metadata": {
                    "search_id": "empty",
                    "keywords": search_request.keywords,
                    "search_date": "",
                    "opportunity_types": search_request.opportunity_types,
                    "total_results": 0
                },
                "opportunities": []
            })
        
        # Step 2: Process with AI
        response = ai_processor.process_search_results(
            search_results=search_results,
            keywords=search_request.keywords,
            opportunity_types=search_request.opportunity_types
        )
        
        # Convert to JSON
        result = response.model_dump()
        
        logger.info(f"Returning {len(result['opportunities'])} opportunities")
        
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return json.dumps({
            "error": str(e),
            "search_metadata": None,
            "opportunities": []
        })


# For local testing
if __name__ == "__main__":
    # Initialize
    init()
    
    # Test request
    test_request = {
        "keywords": ["AI Ethics", "Women in Data Science"],
        "opportunity_types": ["conference", "webinar"],
        "max_results": 10
    }
    
    result = run(json.dumps(test_request))
    print(json.dumps(json.loads(result), indent=2))
