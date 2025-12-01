"""
Model-agnostic AI processor for extracting opportunity information.
Designed to work with any Azure OpenAI chat model.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from openai import AzureOpenAI
import yaml

from models.opportunity import (
    Opportunity,
    SearchMetadata,
    SearchResponse
)
from prompts.extraction_prompt import SYSTEM_PROMPT, get_user_prompt

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIProcessor:
    """
    Model-agnostic AI processor for extracting structured opportunity data.
    
    This class is designed to work with any Azure OpenAI chat model
    without using model-specific parameters like temperature or top_p.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the AI processor.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get credentials from environment
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if not endpoint or not api_key:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY "
                "environment variables must be set"
            )
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=self.config['azure_openai']['api_version']
        )
        
        # Get model deployment name from config (model-agnostic)
        self.chat_deployment = self.config['models']['chat']['deployment_name']
        
        logger.info(f"AI Processor initialized with model: {self.chat_deployment}")
    
    def _call_model(self, system_prompt: str, user_message: str) -> str:
        """
        Call the chat model with given prompts.
        
        NOTE: We intentionally do NOT use temperature, top_p, or other
        model-specific parameters to ensure compatibility with any model.
        
        Args:
            system_prompt: System prompt
            user_message: User message
        
        Returns:
            Model response content
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Model-agnostic call - only required parameters
            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=messages
                # NO temperature, top_p, frequency_penalty, etc.
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error calling AI model: {str(e)}")
            raise
    
    def _parse_opportunities(self, raw_response: str) -> List[dict]:
        """
        Parse the raw model response into opportunity dictionaries.
        
        Args:
            raw_response: Raw text response from the model
        
        Returns:
            List of opportunity dictionaries
        """
        # Try to extract JSON from the response
        try:
            # First, try direct parsing
            opportunities = json.loads(raw_response)
            if isinstance(opportunities, list):
                return opportunities
            elif isinstance(opportunities, dict) and "opportunities" in opportunities:
                return opportunities["opportunities"]
            else:
                return [opportunities]
        
        except json.JSONDecodeError:
            # Try to find JSON array in the response
            start_idx = raw_response.find('[')
            end_idx = raw_response.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                try:
                    json_str = raw_response[start_idx:end_idx]
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON object
            start_idx = raw_response.find('{')
            end_idx = raw_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                try:
                    json_str = raw_response[start_idx:end_idx]
                    result = json.loads(json_str)
                    if isinstance(result, dict):
                        if "opportunities" in result:
                            return result["opportunities"]
                        return [result]
                except json.JSONDecodeError:
                    pass
            
            logger.warning("Could not parse JSON from model response")
            return []
    
    def _validate_and_fix_opportunities(
        self,
        raw_opportunities: List[dict],
        keywords: List[str]
    ) -> List[Opportunity]:
        """
        Validate and fix opportunity data to match our schema.
        
        Args:
            raw_opportunities: Raw opportunity dictionaries from AI
            keywords: Original search keywords
        
        Returns:
            List of validated Opportunity objects
        """
        validated = []
        
        for i, raw in enumerate(raw_opportunities):
            try:
                # Ensure required fields
                if not raw.get("id"):
                    raw["id"] = f"opp_{uuid.uuid4().hex[:8]}"
                
                if not raw.get("event_name"):
                    # Skip opportunities without a name
                    continue
                
                # Add matched keywords if not present
                if not raw.get("keywords_matched"):
                    raw["keywords_matched"] = keywords
                
                # Create Opportunity object (Pydantic handles validation)
                opportunity = Opportunity(**raw)
                validated.append(opportunity)
            
            except Exception as e:
                logger.warning(f"Skipping invalid opportunity {i}: {str(e)}")
                continue
        
        return validated
    
    def process_search_results(
        self,
        search_results: str,
        keywords: List[str],
        opportunity_types: List[str]
    ) -> SearchResponse:
        """
        Process search results and extract structured opportunities.
        
        Args:
            search_results: Formatted search results from Bing
            keywords: Original search keywords
            opportunity_types: Types of opportunities searched for
        
        Returns:
            SearchResponse with extracted opportunities
        """
        logger.info("Processing search results with AI")
        
        # Generate user prompt
        user_prompt = get_user_prompt(keywords, search_results, opportunity_types)
        
        # Call AI model
        raw_response = self._call_model(SYSTEM_PROMPT, user_prompt)
        
        logger.info(f"Received response from AI model ({len(raw_response)} chars)")
        
        # Parse response
        raw_opportunities = self._parse_opportunities(raw_response)
        
        logger.info(f"Parsed {len(raw_opportunities)} raw opportunities")
        
        # Validate and fix
        opportunities = self._validate_and_fix_opportunities(
            raw_opportunities,
            keywords
        )
        
        logger.info(f"Validated {len(opportunities)} opportunities")
        
        # Create response
        metadata = SearchMetadata(
            search_id=f"search_{uuid.uuid4().hex[:12]}",
            keywords=keywords,
            search_date=datetime.utcnow().isoformat(),
            opportunity_types=opportunity_types,
            total_results=len(opportunities)
        )
        
        return SearchResponse(
            search_metadata=metadata,
            opportunities=opportunities
        )
    
    def get_model_info(self) -> dict:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model information
        """
        return {
            "chat_model": self.chat_deployment,
            "api_version": self.config['azure_openai']['api_version']
        }