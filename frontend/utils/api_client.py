"""
API client for communicating with the Opportunity Scout backend.

This client handles all communication with the Azure ML endpoint,
including authentication, request formatting, and error handling.
"""

import requests
import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchRequest:
    """Request model for opportunity search."""
    keywords: List[str]
    opportunity_types: List[str]
    location_preference: str = "global"
    time_frame_months: int = 6
    max_results: int = 20


@dataclass
class Opportunity:
    """Simplified opportunity model for frontend display."""
    id: str
    event_name: str
    event_type: str
    description: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    application_deadline: Optional[str]
    city: Optional[str]
    country: Optional[str]
    is_virtual: bool
    is_paid: bool
    compensation_amount: Optional[float]
    compensation_details: Optional[str]
    application_url: Optional[str]
    source_url: Optional[str]
    confidence_score: float
    keywords_matched: List[str]
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Opportunity":
        """Create Opportunity from API response dictionary."""
        dates = data.get("dates", {})
        location = data.get("location", {})
        compensation = data.get("compensation", {})
        application = data.get("application", {})
        
        return cls(
            id=data.get("id", ""),
            event_name=data.get("event_name", "Unknown Event"),
            event_type=data.get("event_type", "other"),
            description=data.get("description"),
            start_date=dates.get("start_date"),
            end_date=dates.get("end_date"),
            application_deadline=dates.get("application_deadline"),
            city=location.get("city"),
            country=location.get("country"),
            is_virtual=location.get("is_virtual", False),
            is_paid=compensation.get("is_paid", False),
            compensation_amount=compensation.get("amount"),
            compensation_details=compensation.get("details"),
            application_url=application.get("url"),
            source_url=data.get("source_url"),
            confidence_score=data.get("confidence_score", 0.5),
            keywords_matched=data.get("keywords_matched", [])
        )


class OpportunityScoutClient:
    """
    Client for the Opportunity Scout Azure ML endpoint.
    """
    
    def __init__(self, endpoint_url: str, api_key: str):
        """
        Initialize the client.
        
        Args:
            endpoint_url: Azure ML endpoint URL
            api_key: API key for authentication
        """
        self.endpoint_url = endpoint_url.rstrip('/')
        self.api_key = api_key
        
        # Construct the scoring URL
        if not self.endpoint_url.endswith('/score'):
            self.scoring_url = f"{self.endpoint_url}/score"
        else:
            self.scoring_url = self.endpoint_url
    
    def search(self, request: SearchRequest) -> Dict[str, Any]:
        """
        Search for speaking opportunities.
        
        Args:
            request: SearchRequest with search parameters
        
        Returns:
            Dictionary with search results
        
        Raises:
            Exception: If the API call fails
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "azureml-model-deployment": "default"
        }
        
        payload = {
            "keywords": request.keywords,
            "opportunity_types": request.opportunity_types,
            "location_preference": request.location_preference,
            "time_frame_months": request.time_frame_months,
            "max_results": request.max_results
        }
        
        logger.info(f"Sending search request to {self.scoring_url}")
        logger.info(f"Keywords: {request.keywords}")
        
        try:
            response = requests.post(
                self.scoring_url,
                headers=headers,
                json=payload,
                timeout=120  # 2 minute timeout for AI processing
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Handle string response (Azure ML sometimes wraps in string)
            if isinstance(result, str):
                result = json.loads(result)
            
            logger.info(f"Received {len(result.get('opportunities', []))} opportunities")
            
            return result
        
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            raise Exception("Search request timed out. Please try again.")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if response.status_code == 401:
                raise Exception("Authentication failed. Please check your API key.")
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded. Please wait and try again.")
            else:
                raise Exception(f"API error: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"Failed to connect to the search service: {str(e)}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {e}")
            raise Exception("Invalid response from search service")
    
    def parse_opportunities(self, response: Dict[str, Any]) -> List[Opportunity]:
        """
        Parse API response into Opportunity objects.
        
        Args:
            response: Raw API response dictionary
        
        Returns:
            List of Opportunity objects
        """
        opportunities = []
        
        for opp_data in response.get("opportunities", []):
            try:
                opp = Opportunity.from_api_response(opp_data)
                opportunities.append(opp)
            except Exception as e:
                logger.warning(f"Failed to parse opportunity: {e}")
                continue
        
        return opportunities
    
    def health_check(self) -> bool:
        """
        Check if the endpoint is healthy.
        
        Returns:
            True if endpoint is responding, False otherwise
        """
        try:
            # Try a minimal request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(
                self.endpoint_url,
                headers=headers,
                timeout=10
            )
            
            return response.status_code in [200, 405]  # 405 = Method not allowed but endpoint exists
        
        except Exception:
            return False