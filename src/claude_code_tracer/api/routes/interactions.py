"""Interaction-related API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Body

from claude_code_tracer.api.dependencies import (
    OptionalUser,
    SupabaseServiceDep,
)
from claude_code_tracer.models import (
    InteractionInDB,
    InteractionSearchRequest,
    InteractionSearchResponse,
)

router = APIRouter()


@router.get("/{interaction_id}", response_model=InteractionInDB)
async def get_interaction(
    interaction_id: UUID,
    supabase: SupabaseServiceDep,
    user: OptionalUser,
):
    """Get a specific interaction by ID."""
    interaction = await supabase.get_interaction(interaction_id)
    
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    # Check access permissions by verifying session ownership
    session = await supabase.get_session(interaction.session_id)
    if session and user and session.user_id and str(session.user_id) != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return interaction


@router.post("/search", response_model=InteractionSearchResponse)
async def search_interactions(
    request: InteractionSearchRequest = Body(...),
    supabase: SupabaseServiceDep = None,
    user: OptionalUser = None,
):
    """Search interactions by content."""
    # Filter session IDs based on user access
    session_ids = request.session_ids
    
    if user and session_ids:
        # Verify user has access to all requested sessions
        for session_id in session_ids:
            session = await supabase.get_session(session_id)
            if session and session.user_id and str(session.user_id) != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied to session {session_id}",
                )
    
    # Perform search
    if request.query:
        interactions = await supabase.search_interactions(
            query=request.query,
            session_ids=session_ids,
            limit=request.limit,
        )
    else:
        # If no query, just list interactions
        interactions = []
        if session_ids:
            for session_id in session_ids[:request.limit]:
                session_interactions = await supabase.list_interactions(
                    session_id,
                    limit=request.limit // len(session_ids),
                )
                interactions.extend(session_interactions)
    
    return InteractionSearchResponse(
        interactions=interactions[:request.limit],
        total_results=len(interactions),
        query=request.query,
    )


@router.get("/session/{session_id}", response_model=List[InteractionInDB])
async def list_session_interactions(
    session_id: UUID,
    supabase: SupabaseServiceDep,
    user: OptionalUser,
    limit: int = 100,
    offset: int = 0,
):
    """List all interactions for a specific session."""
    # Check session access
    session = await supabase.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if user and session.user_id and str(session.user_id) != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Fetch interactions
    interactions = await supabase.list_interactions(
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    
    return interactions