"""
Data models for speaking opportunities.
Uses Pydantic for validation and serialization.
Updated to handle None values from AI responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class OpportunityType(str, Enum):
    """Types of speaking opportunities."""
    CONFERENCE = "conference"
    SEMINAR = "seminar"
    WEBINAR = "webinar"
    PODCAST = "podcast"
    PANEL = "panel"
    WORKSHOP = "workshop"
    KEYNOTE = "keynote"
    OTHER = "other"


class CompensationType(str, Enum):
    """Types of compensation."""
    PAID = "paid"
    HONORARIUM = "honorarium"
    TRAVEL_ONLY = "travel_only"
    UNPAID = "unpaid"
    NEGOTIABLE = "negotiable"
    UNKNOWN = "unknown"


class DateInfo(BaseModel):
    """Date-related information for an event."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    application_deadline: Optional[str] = None


class Location(BaseModel):
    """Location information for an event."""
    venue: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    is_virtual: Optional[bool] = False
    has_virtual_option: Optional[bool] = False
    
    def __init__(self, **data):
        # Convert None to False for boolean fields
        if data.get('is_virtual') is None:
            data['is_virtual'] = False
        if data.get('has_virtual_option') is None:
            data['has_virtual_option'] = False
        super().__init__(**data)


class Compensation(BaseModel):
    """Compensation details."""
    is_paid: Optional[bool] = False
    compensation_type: Optional[CompensationType] = CompensationType.UNKNOWN
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    includes_travel: Optional[bool] = False
    includes_accommodation: Optional[bool] = False
    details: Optional[str] = None
    
    def __init__(self, **data):
        # Convert None to False for boolean fields
        if data.get('is_paid') is None:
            data['is_paid'] = False
        if data.get('includes_travel') is None:
            data['includes_travel'] = False
        if data.get('includes_accommodation') is None:
            data['includes_accommodation'] = False
        if data.get('compensation_type') is None:
            data['compensation_type'] = CompensationType.UNKNOWN
        super().__init__(**data)


class ApplicationInfo(BaseModel):
    """Application-related information."""
    url: Optional[str] = None
    contact_email: Optional[str] = None
    requirements: Optional[List[str]] = Field(default_factory=list)
    
    def __init__(self, **data):
        if data.get('requirements') is None:
            data['requirements'] = []
        super().__init__(**data)


class Opportunity(BaseModel):
    """
    Complete model for a speaking opportunity.
    All fields are Optional to handle incomplete AI responses.
    """
    id: str
    event_name: str
    event_type: Optional[OpportunityType] = OpportunityType.OTHER
    description: Optional[str] = None
    dates: Optional[DateInfo] = Field(default_factory=DateInfo)
    location: Optional[Location] = Field(default_factory=Location)
    compensation: Optional[Compensation] = Field(default_factory=Compensation)
    application: Optional[ApplicationInfo] = Field(default_factory=ApplicationInfo)
    target_audience: Optional[List[str]] = Field(default_factory=list)
    expected_audience_size: Optional[str] = None
    keywords_matched: Optional[List[str]] = Field(default_factory=list)
    source_url: Optional[str] = None
    confidence_score: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    
    def __init__(self, **data):
        # Handle None values for nested objects
        if data.get('dates') is None:
            data['dates'] = {}
        if data.get('location') is None:
            data['location'] = {}
        if data.get('compensation') is None:
            data['compensation'] = {}
        if data.get('application') is None:
            data['application'] = {}
        if data.get('target_audience') is None:
            data['target_audience'] = []
        if data.get('keywords_matched') is None:
            data['keywords_matched'] = []
        if data.get('event_type') is None:
            data['event_type'] = OpportunityType.OTHER
        if data.get('confidence_score') is None:
            data['confidence_score'] = 0.5
        super().__init__(**data)


class SearchMetadata(BaseModel):
    """Metadata about the search performed."""
    search_id: str
    keywords: List[str]
    search_date: str
    opportunity_types: List[str]
    location_preference: Optional[str] = None
    total_results: int = 0


class SearchResponse(BaseModel):
    """
    Complete response from a search operation.
    This is what gets saved to JSON.
    """
    search_metadata: SearchMetadata
    opportunities: List[Opportunity] = Field(default_factory=list)


class SearchRequest(BaseModel):
    """
    Input request for searching opportunities.
    """
    keywords: List[str]
    opportunity_types: List[str] = Field(
        default_factory=lambda: ["conference", "seminar", "webinar"]
    )
    location_preference: Optional[str] = "global"
    time_frame_months: int = Field(default=6, ge=1, le=12)
    max_results: int = Field(default=20, ge=1, le=50)
