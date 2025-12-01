"""
Service for ranking opportunities based on candidate profile.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RankingService:
    """
    Service for ranking opportunities against candidate profiles.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the ranking service."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if not endpoint or not api_key:
            raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set")
        
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=self.config['azure_openai']['api_version']
        )
        
        self.chat_deployment = self.config['models']['chat']['deployment_name']
        logger.info(f"RankingService initialized with model: {self.chat_deployment}")
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse a date string into datetime object."""
        if not date_str:
            return None
        
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%B %d, %Y",
            "%b %d, %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _is_expired(self, opportunity: Dict[str, Any], current_date: datetime) -> bool:
        """Check if an opportunity's deadline has passed."""
        dates = opportunity.get("dates", {})
        deadline_str = dates.get("application_deadline")
        
        if not deadline_str:
            # If no deadline, check start date
            start_str = dates.get("start_date")
            if start_str:
                start_date = self._parse_date(start_str)
                if start_date and start_date < current_date:
                    return True
            return False
        
        deadline = self._parse_date(deadline_str)
        if deadline:
            return deadline < current_date
        
        return False
    
    def _days_until_deadline(self, opportunity: Dict[str, Any], current_date: datetime) -> Optional[int]:
        """Calculate days until deadline."""
        dates = opportunity.get("dates", {})
        deadline_str = dates.get("application_deadline")
        
        if not deadline_str:
            return None
        
        deadline = self._parse_date(deadline_str)
        if deadline:
            delta = deadline - current_date
            return delta.days
        
        return None
    
    def _prepare_opportunity_text(self, opportunity: Dict[str, Any]) -> str:
        """Convert opportunity to text for AI processing."""
        parts = []
        
        parts.append(f"ID: {opportunity.get('id', 'unknown')}")
        parts.append(f"Event: {opportunity.get('event_name', 'Unknown Event')}")
        parts.append(f"Type: {opportunity.get('event_type', 'unknown')}")
        
        if opportunity.get("description"):
            parts.append(f"Description: {opportunity['description']}")
        
        dates = opportunity.get("dates", {})
        if dates.get("start_date"):
            parts.append(f"Start Date: {dates['start_date']}")
        if dates.get("end_date"):
            parts.append(f"End Date: {dates['end_date']}")
        if dates.get("application_deadline"):
            parts.append(f"Application Deadline: {dates['application_deadline']}")
        
        location = opportunity.get("location", {})
        loc_parts = []
        if location.get("city"):
            loc_parts.append(location["city"])
        if location.get("country"):
            loc_parts.append(location["country"])
        if loc_parts:
            parts.append(f"Location: {', '.join(loc_parts)}")
        if location.get("is_virtual"):
            parts.append("Format: Virtual")
        
        compensation = opportunity.get("compensation", {})
        if compensation.get("is_paid"):
            amount = compensation.get("amount")
            if amount:
                parts.append(f"Compensation: ${amount}")
            else:
                parts.append("Compensation: Paid")
        else:
            parts.append("Compensation: Unpaid/Unknown")
        
        if opportunity.get("keywords_matched"):
            parts.append(f"Keywords: {', '.join(opportunity['keywords_matched'])}")
        
        return "\n".join(parts)
    
    def rank_opportunities_with_ai(
        self,
        profile_summary: str,
        opportunities: List[Dict[str, Any]],
        current_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Use AI to rank opportunities based on profile match.
        
        Args:
            profile_summary: Summary of candidate profile
            opportunities: List of opportunities to rank
            current_date: Current date for deadline checking
        
        Returns:
            List of ranked opportunities with scores
        """
        # Prepare opportunities text
        opp_texts = []
        for opp in opportunities:
            opp_text = self._prepare_opportunity_text(opp)
            opp_texts.append(opp_text)
        
        opportunities_text = "\n\n---\n\n".join(opp_texts)
        current_date_str = current_date.strftime("%Y-%m-%d")
        
        system_prompt = """You are an expert career advisor specializing in matching speakers with speaking opportunities.

Analyze the candidate profile and rank the opportunities based on:
1. Expertise match - how well the candidate's skills match the opportunity
2. Experience level - is the candidate qualified for this opportunity
3. Preferences - does it match their stated preferences
4. Deadline - filter out expired opportunities

Return a JSON array sorted by match_score (highest first)."""

        user_prompt = f"""Please rank the following speaking opportunities for this candidate.

**CURRENT DATE:** {current_date_str}

**CANDIDATE PROFILE:**
{profile_summary}

**OPPORTUNITIES TO RANK:**
{opportunities_text}

**INSTRUCTIONS:**
1. Filter out any opportunities with expired deadlines (before {current_date_str})
2. Score each valid opportunity from 0.0 to 1.0 based on match quality
3. Identify specific reasons for the match
4. List matching keywords

**OUTPUT FORMAT:**
Return a JSON array:
[
  {{
    "opportunity_id": "the id",
    "event_name": "event name",
    "match_score": 0.85,
    "relevance_score": 0.9,
    "preference_score": 0.8,
    "match_reasons": ["Reason 1", "Reason 2"],
    "matching_keywords": ["keyword1", "keyword2"],
    "is_expired": false,
    "days_until_deadline": 30
  }}
]

Sort by match_score descending. Return ONLY the JSON array."""

        try:
            response = self.client.chat.completions.create(
                model=self.chat_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON from response
            try:
                rankings = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to find JSON array in response
                start_idx = result_text.find('[')
                end_idx = result_text.rfind(']') + 1
                if start_idx != -1 and end_idx > start_idx:
                    rankings = json.loads(result_text[start_idx:end_idx])
                else:
                    logger.error("Could not parse rankings from AI response")
                    rankings = []
            
            return rankings
        
        except Exception as e:
            logger.error(f"Error ranking with AI: {e}")
            return []
    
    def rank_opportunities(
        self,
        profile_summary: str,
        opportunities: List[Dict[str, Any]],
        embedding_service=None,
        profile_embedding: List[float] = None
    ) -> Dict[str, Any]:
        """
        Rank opportunities based on profile match.
        
        Uses both AI ranking and optional embedding similarity.
        
        Args:
            profile_summary: Summary of candidate profile
            opportunities: List of opportunities to rank
            embedding_service: Optional embedding service for similarity
            profile_embedding: Optional pre-computed profile embedding
        
        Returns:
            Dictionary with ranked opportunities and metadata
        """
        current_date = datetime.utcnow()
        
        # Filter out clearly expired opportunities first
        valid_opportunities = []
        expired_count = 0
        
        for opp in opportunities:
            if self._is_expired(opp, current_date):
                expired_count += 1
            else:
                valid_opportunities.append(opp)
        
        logger.info(f"Filtered {expired_count} expired opportunities, {len(valid_opportunities)} valid")
        
        if not valid_opportunities:
            return {
                "ranked_opportunities": [],
                "total_opportunities": len(opportunities),
                "valid_opportunities": 0,
                "expired_opportunities": expired_count
            }
        
        # Get AI rankings
        ai_rankings = self.rank_opportunities_with_ai(
            profile_summary,
            valid_opportunities,
            current_date
        )
        
        # Create a lookup for AI rankings
        ai_ranking_lookup = {r["opportunity_id"]: r for r in ai_rankings}
        
        # Combine with original opportunity data
        ranked_results = []
        
        for opp in valid_opportunities:
            opp_id = opp.get("id", "")
            ai_ranking = ai_ranking_lookup.get(opp_id, {})
            
            # Get location string
            location = opp.get("location", {})
            loc_parts = []
            if location.get("city"):
                loc_parts.append(location["city"])
            if location.get("country"):
                loc_parts.append(location["country"])
            location_str = ", ".join(loc_parts) if loc_parts else None
            
            # Get compensation info
            compensation = opp.get("compensation", {})
            
            ranked_opp = {
                "opportunity_id": opp_id,
                "event_name": opp.get("event_name", "Unknown Event"),
                "event_type": opp.get("event_type"),
                "description": opp.get("description"),
                "start_date": opp.get("dates", {}).get("start_date"),
                "end_date": opp.get("dates", {}).get("end_date"),
                "application_deadline": opp.get("dates", {}).get("application_deadline"),
                "location": location_str,
                "is_virtual": location.get("is_virtual", False),
                "is_paid": compensation.get("is_paid", False),
                "compensation_amount": compensation.get("amount"),
                "application_url": opp.get("application", {}).get("url"),
                "source_url": opp.get("source_url"),
                "match_score": ai_ranking.get("match_score", 0.5),
                "relevance_score": ai_ranking.get("relevance_score", 0.5),
                "preference_score": ai_ranking.get("preference_score", 0.5),
                "match_reasons": ai_ranking.get("match_reasons", []),
                "matching_keywords": ai_ranking.get("matching_keywords", []),
                "is_expired": False,
                "days_until_deadline": self._days_until_deadline(opp, current_date)
            }
            
            ranked_results.append(ranked_opp)
        
        # Sort by match score
        ranked_results.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "ranked_opportunities": ranked_results,
            "total_opportunities": len(opportunities),
            "valid_opportunities": len(valid_opportunities),
            "expired_opportunities": expired_count
        }