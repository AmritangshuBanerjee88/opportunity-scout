"""Models package for Proposal Architect."""

from .profile import (
    CandidateProfile,
    CandidatePreferences,
    ProfileChunk,
    UploadRequest
)
from .proposal import (
    RankedOpportunity,
    GeneratedProposal,
    RankingResponse,
    ProposalResponse,
    BatchProposalResponse
)

__all__ = [
    "CandidateProfile",
    "CandidatePreferences",
    "ProfileChunk",
    "UploadRequest",
    "RankedOpportunity",
    "GeneratedProposal",
    "RankingResponse",
    "ProposalResponse",
    "BatchProposalResponse"
]
