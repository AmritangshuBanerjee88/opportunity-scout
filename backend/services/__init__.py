"""Services package."""

from .serper_search import SerperSearchService
from .ai_processor import AIProcessor

# Backward compatibility
BingSearchService = SerperSearchService

__all__ = [
    "SerperSearchService",
    "BingSearchService",  # Alias for backward compatibility
    "AIProcessor"
]
