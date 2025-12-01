"""
Azure ML Scoring Script for Proposal Architect.

This script handles incoming requests to the Azure ML endpoint
and orchestrates profile parsing, ranking, and proposal generation.
"""

import os
import json
import logging
import sys
import uuid
from datetime import datetime

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.profile_parser import ProfileParserService
from services.embedding_service import EmbeddingService
from services.search_service import AzureSearchService
from services.ranking_service import RankingService
from services.proposal_generator import ProposalGeneratorService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances (initialized once)
profile_parser = None
embedding_service = None
search_service = None
ranking_service = None
proposal_generator = None

# Session storage (in-memory for simplicity)
sessions = {}


def init():
    """
    Initialize the scoring script.
    Called once when the endpoint starts.
    """
    global profile_parser, embedding_service, search_service, ranking_service, proposal_generator
    
    logger.info("Initializing Proposal Architect endpoint...")
    
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config.yaml"
        )
        
        profile_parser = ProfileParserService(config_path)
        embedding_service = EmbeddingService(config_path)
        search_service = AzureSearchService(config_path)
        ranking_service = RankingService(config_path)
        proposal_generator = ProposalGeneratorService(config_path)
        
        # Create search index if it doesn't exist
        search_service.create_index()
        
        logger.info("Initialization complete!")
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        raise


def handle_upload(request_data: dict) -> dict:
    """
    Handle profile and opportunities upload.
    
    Expected input:
    {
        "action": "upload",
        "opportunities_json": "...",  # JSON string of opportunities
        "profile_text": "...",         # Optional plain text profile
        "resume_base64": "...",        # Optional base64 encoded resume
        "resume_filename": "...",      # Optional resume filename
        "preferences_text": "..."      # Optional preferences
    }
    """
    session_id = str(uuid.uuid4())
    logger.info(f"Processing upload for session: {session_id}")
    
    try:
        # Parse opportunities
        opportunities_json = request_data.get("opportunities_json", "{}")
        if isinstance(opportunities_json, str):
            opportunities_data = json.loads(opportunities_json)
        else:
            opportunities_data = opportunities_json
        
        opportunities = opportunities_data.get("opportunities", [])
        logger.info(f"Received {len(opportunities)} opportunities")
        
        # Parse resume if provided
        resume_content = None
        resume_filename = request_data.get("resume_filename")
        if request_data.get("resume_base64"):
            import base64
            resume_content = base64.b64decode(request_data["resume_base64"])
        
        # Parse profile
        profile_result = profile_parser.parse_profile(
            profile_text=request_data.get("profile_text"),
            resume_content=resume_content,
            resume_filename=resume_filename,
            preferences_text=request_data.get("preferences_text")
        )
        
        logger.info(f"Profile parsed: {profile_result['profile_id']}")
        
        # Store in session
        sessions[session_id] = {
            "profile": profile_result,
            "opportunities": opportunities,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Index documents in Azure Search for RAG
        documents_to_index = []
        
        # Index profile chunks
        profile_text = profile_result.get("raw_text", "")
        if profile_text:
            chunks = embedding_service.chunk_text(profile_text)
            for i, chunk in enumerate(chunks):
                embedding = embedding_service.generate_embedding(chunk)
                if embedding:
                    documents_to_index.append({
                        "id": f"{session_id}_profile_{i}",
                        "session_id": session_id,
                        "document_type": "profile",
                        "title": f"Profile Chunk {i+1}",
                        "content": chunk,
                        "embedding": embedding,
                        "metadata": {"chunk_index": i}
                    })
        
        # Index opportunities
        for opp in opportunities:
            opp_text = f"{opp.get('event_name', '')} - {opp.get('description', '')} - {opp.get('event_type', '')}"
            embedding = embedding_service.generate_embedding(opp_text)
            if embedding:
                documents_to_index.append({
                    "id": f"{session_id}_opp_{opp.get('id', uuid.uuid4())}",
                    "session_id": session_id,
                    "document_type": "opportunity",
                    "title": opp.get("event_name", "Unknown"),
                    "content": opp_text,
                    "embedding": embedding,
                    "metadata": opp
                })
        
        if documents_to_index:
            search_service.index_documents(documents_to_index)
            logger.info(f"Indexed {len(documents_to_index)} documents")
        
        return {
            "success": True,
            "session_id": session_id,
            "profile_summary": profile_result.get("profile_summary", ""),
            "opportunities_count": len(opportunities),
            "message": "Upload successful. Ready for ranking."
        }
    
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def handle_rank(request_data: dict) -> dict:
    """
    Handle ranking request.
    
    Expected input:
    {
        "action": "rank",
        "session_id": "..."
    }
    """
    session_id = request_data.get("session_id")
    
    if not session_id or session_id not in sessions:
        return {
            "success": False,
            "error": "Invalid or expired session. Please upload data first."
        }
    
    logger.info(f"Ranking opportunities for session: {session_id}")
    
    try:
        session = sessions[session_id]
        profile = session["profile"]
        opportunities = session["opportunities"]
        
        # Rank opportunities
        ranking_result = ranking_service.rank_opportunities(
            profile_summary=profile.get("profile_summary", ""),
            opportunities=opportunities,
            embedding_service=embedding_service
        )
        
        # Store rankings in session
        sessions[session_id]["rankings"] = ranking_result
        
        logger.info(f"Ranked {ranking_result['valid_opportunities']} opportunities")
        
        return {
            "success": True,
            "session_id": session_id,
            "profile_summary": profile.get("profile_summary", ""),
            "total_opportunities": ranking_result["total_opportunities"],
            "valid_opportunities": ranking_result["valid_opportunities"],
            "expired_opportunities": ranking_result["expired_opportunities"],
            "ranked_opportunities": ranking_result["ranked_opportunities"]
        }
    
    except Exception as e:
        logger.error(f"Ranking failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def handle_generate_proposal(request_data: dict) -> dict:
    """
    Handle proposal generation for a single opportunity.
    
    Expected input:
    {
        "action": "generate_proposal",
        "session_id": "...",
        "opportunity_id": "..."
    }
    """
    session_id = request_data.get("session_id")
    opportunity_id = request_data.get("opportunity_id")
    
    if not session_id or session_id not in sessions:
        return {
            "success": False,
            "error": "Invalid or expired session."
        }
    
    logger.info(f"Generating proposal for opportunity: {opportunity_id}")
    
    try:
        session = sessions[session_id]
        profile = session["profile"]
        rankings = session.get("rankings", {})
        ranked_opps = rankings.get("ranked_opportunities", [])
        
        # Find the opportunity
        opportunity = None
        for opp in ranked_opps:
            if opp.get("opportunity_id") == opportunity_id:
                opportunity = opp
                break
        
        if not opportunity:
            return {
                "success": False,
                "error": f"Opportunity {opportunity_id} not found in rankings."
            }
        
        # Generate proposal
        proposal = proposal_generator.generate_proposal(
            profile_summary=profile.get("profile_summary", ""),
            opportunity=opportunity,
            matching_keywords=opportunity.get("matching_keywords", []),
            match_reasons=opportunity.get("match_reasons", [])
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "proposal": proposal
        }
    
    except Exception as e:
        logger.error(f"Proposal generation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def handle_generate_all_proposals(request_data: dict) -> dict:
    """
    Handle batch proposal generation.
    
    Expected input:
    {
        "action": "generate_all_proposals",
        "session_id": "...",
        "max_proposals": 5
    }
    """
    session_id = request_data.get("session_id")
    max_proposals = request_data.get("max_proposals", 5)
    
    if not session_id or session_id not in sessions:
        return {
            "success": False,
            "error": "Invalid or expired session."
        }
    
    logger.info(f"Generating {max_proposals} proposals for session: {session_id}")
    
    try:
        session = sessions[session_id]
        profile = session["profile"]
        rankings = session.get("rankings", {})
        ranked_opps = rankings.get("ranked_opportunities", [])
        
        if not ranked_opps:
            return {
                "success": False,
                "error": "No ranked opportunities. Please run ranking first."
            }
        
        # Generate proposals
        proposals = proposal_generator.generate_proposals_batch(
            profile_summary=profile.get("profile_summary", ""),
            ranked_opportunities=ranked_opps,
            max_proposals=max_proposals
        )
        
        # Format for download
        download_text = proposal_generator.format_all_proposals_for_download(proposals)
        
        return {
            "success": True,
            "session_id": session_id,
            "proposals": proposals,
            "download_text": download_text,
            "total_generated": len(proposals)
        }
    
    except Exception as e:
        logger.error(f"Batch proposal generation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def run(raw_data: str) -> str:
    """
    Process incoming requests.
    
    Args:
        raw_data: JSON string with request data
    
    Returns:
        JSON string with response
    """
    logger.info("Received request")
    
    try:
        request_data = json.loads(raw_data)
        action = request_data.get("action", "")
        
        logger.info(f"Action: {action}")
        
        if action == "upload":
            result = handle_upload(request_data)
        elif action == "rank":
            result = handle_rank(request_data)
        elif action == "generate_proposal":
            result = handle_generate_proposal(request_data)
        elif action == "generate_all_proposals":
            result = handle_generate_all_proposals(request_data)
        elif action == "health":
            result = {"success": True, "status": "healthy"}
        else:
            result = {
                "success": False,
                "error": f"Unknown action: {action}. Valid actions: upload, rank, generate_proposal, generate_all_proposals"
            }
        
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


# For local testing
if __name__ == "__main__":
    init()
    
    # Test health check
    result = run(json.dumps({"action": "health"}))
    print(result)