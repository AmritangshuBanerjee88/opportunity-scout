"""Prompts package for Proposal Architect."""

from .ranking_prompt import (
    RANKING_SYSTEM_PROMPT,
    get_ranking_user_prompt,
    PROFILE_EXTRACTION_PROMPT,
    get_profile_extraction_user_prompt
)
from .proposal_prompt import (
    PROPOSAL_SYSTEM_PROMPT,
    get_proposal_user_prompt,
    get_batch_proposal_prompt
)

__all__ = [
    "RANKING_SYSTEM_PROMPT",
    "get_ranking_user_prompt",
    "PROFILE_EXTRACTION_PROMPT",
    "get_profile_extraction_user_prompt",
    "PROPOSAL_SYSTEM_PROMPT",
    "get_proposal_user_prompt",
    "get_batch_proposal_prompt"
]