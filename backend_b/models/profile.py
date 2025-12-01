"""
Data models for candidate profiles.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CandidatePreferences(BaseModel):
    """Candidate's preferences for opportunities."""
    preferred_compensation: Optional[str] = "any"  # "paid", "unpaid", "any"
    minimum_fee: Optional[float] = None
    preferred_locations: List[str] = Field(default_factory=list)
    willing_to_travel: bool = True
    preferred_formats: List[str] = Field(default_factory=lambda: ["conference", "webinar", "podcast"])
    available_from: Optional[str] = None
    available_until: Optional[str] = None
    topics_of_interest: List[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    """Complete candidate profile."""
    id: str
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    
    # Expertise
    primary_expertise: List[str] = Field(default_factory=list)
    secondary_expertise: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    
    # Experience
    years_of_experience: Optional[int] = None
    speaking_experience: Optional[str] = None
    notable_talks: List[str] = Field(default_factory=list)
    notable_venues: List[str] = Field(default_factory=list)
    
    # Credentials
    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    publications: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)
    
    # Bio and summary
    bio: Optional[str] = None
    summary: Optional[str] = None
    
    # Raw text (for embedding)
    raw_text: Optional[str] = None
    
    # Preferences
    preferences: CandidatePreferences = Field(default_factory=CandidatePreferences)
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProfileChunk(BaseModel):
    """A chunk of profile text for embedding."""
    id: str
    profile_id: str
    chunk_type: str  # "bio", "experience", "expertise", "preferences"
    text: str
    embedding: Optional[List[float]] = None


class UploadRequest(BaseModel):
    """Request to upload profile and opportunities."""
    opportunities_json: str  # JSON string of opportunities
    profile_text: Optional[str] = None  # Plain text profile/bio
    resume_text: Optional[str] = None  # Extracted text from resume
    preferences_text: Optional[str] = None  # User preferences as text
    
    # Structured preferences (optional)
    preferred_compensation: Optional[str] = "any"
    minimum_fee: Optional[float] = None
    preferred_locations: Optional[str] = None  # Comma-separated
    willing_to_travel: bool = True
    available_from: Optional[str] = None
    available_until: Optional[str] = None
