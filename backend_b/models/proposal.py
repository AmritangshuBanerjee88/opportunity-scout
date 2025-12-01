"""
Data models for proposals and rankings.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RankedOpportunity(BaseModel):
    """An opportunity with ranking information."""
    opportunity_id: str
    event_name: str
    event_type: Optional[str] = None
    
    # Ranking details
    match_score: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    preference_score: float = Field(ge=0.0, le=1.0)
    
    # Match reasons
    match_reasons: List[str] = Field(default_factory=list)
    matching_keywords: List[str] = Field(default_factory=list)
    
    # Opportunity details (copied from original)
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    application_deadline: Optional[str] = None
    location: Optional[str] = None
    is_virtual: bool = False
    is_paid: bool = False
    compensation_amount: Optional[float] = None
    application_url: Optional[str] = None
    source_url: Optional[str] = None
    
    # Status
    is_expired: bool = False
    days_until_deadline: Optional[int] = None


class GeneratedProposal(BaseModel):
    """A generated proposal/pitch for an opportunity."""
    id: str
    opportunity_id: str
    event_name: str
    
    # Proposal content
    subject_line: str
    greeting: str
    opening_paragraph: str
    value_proposition: str
    relevant_experience: str
    proposed_topics: List[str] = Field(default_factory=list)
    closing_paragraph: str
    signature: str
    
    # Full proposal text
    full_proposal: str
    
    # Metadata
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    word_count: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.full_proposal:
            self.word_count = len(self.full_proposal.split())


class RankingResponse(BaseModel):
    """Response from ranking operation."""
    session_id: str
    profile_summary: str
    total_opportunities: int
    valid_opportunities: int
    expired_opportunities: int
    ranked_opportunities: List[RankedOpportunity] = Field(default_factory=list)
    ranking_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProposalResponse(BaseModel):
    """Response from proposal generation."""
    session_id: str
    opportunity_id: str
    proposal: GeneratedProposal
    generation_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BatchProposalResponse(BaseModel):
    """Response from batch proposal generation."""
    session_id: str
    proposals: List[GeneratedProposal] = Field(default_factory=list)
    total_generated: int = 0
    generation_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
