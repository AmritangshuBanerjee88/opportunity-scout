"""Prompts package."""

from .extraction_prompt import (
    SYSTEM_PROMPT,
    get_user_prompt,
    get_refinement_prompt
)

__all__ = [
    "SYSTEM_PROMPT",
    "get_user_prompt",
    "get_refinement_prompt"
]
