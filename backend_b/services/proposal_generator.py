"""
Service for generating personalized proposals/pitches.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProposalGeneratorService:
    """
    Service for generating personalized speaker proposals.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the proposal generator service."""
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
        logger.info(f"ProposalGeneratorService initialized with model: {self.chat_deployment}")
    
    def _prepare_opportunity_details(self, opportunity: Dict[str, Any]) -> str:
        """Convert opportunity to detailed text for proposal generation."""
        parts = []
        
        parts.append(f"Event Name: {opportunity.get('event_name', 'Unknown Event')}")
        parts.append(f"Event Type: {opportunity.get('event_type', 'unknown')}")
        
        if opportunity.get("description"):
            parts.append(f"Description: {opportunity['description']}")
        
        if opportunity.get("start_date"):
            parts.append(f"Event Date: {opportunity['start_date']}")
        
        if opportunity.get("application_deadline"):
            parts.append(f"Application Deadline: {opportunity['application_deadline']}")
        
        if opportunity.get("location"):
            parts.append(f"Location: {opportunity['location']}")
        
        if opportunity.get("is_virtual"):
            parts.append("Format: Virtual/Online")
        
        if opportunity.get("is_paid"):
            amount = opportunity.get("compensation_amount")
            if amount:
                parts.append(f"Compensation: ${amount}")
            else:
                parts.append("Compensation: Paid opportunity")
        
        if opportunity.get("application_url"):
            parts.append(f"Application URL: {opportunity['application_url']}")
        
        return "\n".join(parts)
    
    def generate_proposal(
        self,
        profile_summary: str,
        opportunity: Dict[str, Any],
        matching_keywords: List[str] = None,
        match_reasons: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized proposal for a single opportunity.
        
        Args:
            profile_summary: Summary of candidate profile
            opportunity: Opportunity details
            matching_keywords: Keywords that match between profile and opportunity
            match_reasons: Reasons why this is a good match
        
        Returns:
            Generated proposal dictionary
        """
        opportunity_details = self._prepare_opportunity_details(opportunity)
        
        keywords_str = ", ".join(matching_keywords) if matching_keywords else "N/A"
        reasons_str = "\n".join([f"- {r}" for r in match_reasons]) if match_reasons else "N/A"
        
        system_prompt = """You are an expert proposal writer specializing in crafting compelling speaker applications.

Write personalized, professional proposals that:
1. Grab attention with a strong opening
2. Clearly articulate the speaker's unique value
3. Highlight relevant experience and credentials
4. Propose specific, relevant topics
5. End with a clear call to action

Be confident but not arrogant. Be specific, not generic."""

        user_prompt = f"""Please write a compelling speaker proposal for this opportunity.

**CANDIDATE PROFILE:**
{profile_summary}

**OPPORTUNITY DETAILS:**
{opportunity_details}

**WHY THIS IS A GOOD MATCH:**
{reasons_str}

**MATCHING KEYWORDS:**
{keywords_str}

**INSTRUCTIONS:**
Write a complete proposal including:
1. Compelling subject line
2. Professional greeting
3. Strong opening paragraph
4. Value proposition
5. Relevant experience
6. 2-3 proposed talk topics
7. Closing with call to action
8. Professional signature

**OUTPUT FORMAT:**
Return a JSON object:
{{
  "subject_line": "Compelling subject line",
  "greeting": "Dear [Event Organizers],",
  "opening_paragraph": "Opening that grabs attention...",
  "value_proposition": "What unique value the speaker brings...",
  "relevant_experience": "Specific relevant experience...",
  "proposed_topics": [
    "Topic 1: Brief description",
    "Topic 2: Brief description",
    "Topic 3: Brief description"
  ],
  "closing_paragraph": "Strong closing with call to action...",
  "signature": "Best regards,\\n[Name]\\n[Title]",
  "full_proposal": "The complete proposal as formatted text..."
}}

Return ONLY the JSON object."""

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
                proposal_data = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to find JSON in response
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    proposal_data = json.loads(result_text[start_idx:end_idx])
                else:
                    logger.error("Could not parse proposal from AI response")
                    proposal_data = self._create_fallback_proposal(profile_summary, opportunity)
            
            # Add metadata
            proposal_data["id"] = str(uuid.uuid4())
            proposal_data["opportunity_id"] = opportunity.get("opportunity_id", opportunity.get("id", ""))
            proposal_data["event_name"] = opportunity.get("event_name", "Unknown Event")
            proposal_data["generated_at"] = datetime.utcnow().isoformat()
            
            if proposal_data.get("full_proposal"):
                proposal_data["word_count"] = len(proposal_data["full_proposal"].split())
            else:
                proposal_data["word_count"] = 0
            
            return proposal_data
        
        except Exception as e:
            logger.error(f"Error generating proposal: {e}")
            return self._create_fallback_proposal(profile_summary, opportunity)
    
    def _create_fallback_proposal(self, profile_summary: str, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic fallback proposal if AI fails."""
        event_name = opportunity.get("event_name", "your event")
        
        return {
            "id": str(uuid.uuid4()),
            "opportunity_id": opportunity.get("opportunity_id", opportunity.get("id", "")),
            "event_name": event_name,
            "subject_line": f"Speaker Proposal for {event_name}",
            "greeting": "Dear Event Organizers,",
            "opening_paragraph": f"I am writing to express my interest in speaking at {event_name}.",
            "value_proposition": "I bring a unique perspective combining practical experience with thought leadership in this space.",
            "relevant_experience": "Please see my attached resume for details on my relevant experience.",
            "proposed_topics": ["Topic to be discussed based on event needs"],
            "closing_paragraph": "I would welcome the opportunity to discuss how I can contribute to your event. Please feel free to reach out at your convenience.",
            "signature": "Best regards",
            "full_proposal": f"Dear Event Organizers,\n\nI am writing to express my interest in speaking at {event_name}.\n\nI bring a unique perspective combining practical experience with thought leadership in this space.\n\nI would welcome the opportunity to discuss how I can contribute to your event.\n\nBest regards",
            "generated_at": datetime.utcnow().isoformat(),
            "word_count": 50
        }
    
    def generate_proposals_batch(
        self,
        profile_summary: str,
        ranked_opportunities: List[Dict[str, Any]],
        max_proposals: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate proposals for multiple opportunities.
        
        Args:
            profile_summary: Summary of candidate profile
            ranked_opportunities: List of ranked opportunities
            max_proposals: Maximum number of proposals to generate
        
        Returns:
            List of generated proposals
        """
        proposals = []
        
        # Take top opportunities
        top_opportunities = ranked_opportunities[:max_proposals]
        
        for i, opp in enumerate(top_opportunities):
            logger.info(f"Generating proposal {i+1}/{len(top_opportunities)} for {opp.get('event_name', 'Unknown')}")
            
            proposal = self.generate_proposal(
                profile_summary=profile_summary,
                opportunity=opp,
                matching_keywords=opp.get("matching_keywords", []),
                match_reasons=opp.get("match_reasons", [])
            )
            
            proposals.append(proposal)
        
        logger.info(f"Generated {len(proposals)} proposals")
        return proposals
    
    def format_proposal_for_download(self, proposal: Dict[str, Any]) -> str:
        """
        Format a proposal for downloading as text.
        
        Args:
            proposal: Proposal dictionary
        
        Returns:
            Formatted text string
        """
        lines = []
        
        lines.append("=" * 60)
        lines.append(f"PROPOSAL FOR: {proposal.get('event_name', 'Unknown Event')}")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append(f"Subject: {proposal.get('subject_line', 'N/A')}")
        lines.append("")
        lines.append("-" * 40)
        lines.append("")
        
        if proposal.get("full_proposal"):
            lines.append(proposal["full_proposal"])
        else:
            lines.append(proposal.get("greeting", ""))
            lines.append("")
            lines.append(proposal.get("opening_paragraph", ""))
            lines.append("")
            lines.append(proposal.get("value_proposition", ""))
            lines.append("")
            lines.append(proposal.get("relevant_experience", ""))
            lines.append("")
            
            if proposal.get("proposed_topics"):
                lines.append("Proposed Topics:")
                for topic in proposal["proposed_topics"]:
                    lines.append(f"  • {topic}")
                lines.append("")
            
            lines.append(proposal.get("closing_paragraph", ""))
            lines.append("")
            lines.append(proposal.get("signature", ""))
        
        lines.append("")
        lines.append("-" * 40)
        lines.append(f"Generated: {proposal.get('generated_at', 'N/A')}")
        lines.append(f"Word Count: {proposal.get('word_count', 'N/A')}")
        lines.append("")
        
        return "\n".join(lines)
    
    def format_all_proposals_for_download(self, proposals: List[Dict[str, Any]]) -> str:
        """
        Format all proposals for downloading as a single text file.
        
        Args:
            proposals: List of proposal dictionaries
        
        Returns:
            Formatted text string with all proposals
        """
        lines = []
        
        lines.append("=" * 60)
        lines.append("GENERATED SPEAKER PROPOSALS")
        lines.append(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"Total Proposals: {len(proposals)}")
        lines.append("=" * 60)
        lines.append("")
        lines.append("")
        
        for i, proposal in enumerate(proposals, 1):
            lines.append(f"PROPOSAL {i} OF {len(proposals)}")
            lines.append(self.format_proposal_for_download(proposal))
            lines.append("")
            lines.append("")
        
        return "\n".join(lines)