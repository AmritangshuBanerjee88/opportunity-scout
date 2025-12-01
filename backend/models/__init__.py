"""Models package."""

from .opportunity import (
    Opportunity,
    OpportunityType,
    CompensationType,
    DateInfo,
    Location,
    Compensation,
    ApplicationInfo,
    SearchMetadata,
    SearchResponse,
    SearchRequest
)

__all__ = [
    "Opportunity",
    "OpportunityType", 
    "CompensationType",
    "DateInfo",
    "Location",
    "Compensation",
    "ApplicationInfo",
    "SearchMetadata",
    "SearchResponse",
    "SearchRequest"
]