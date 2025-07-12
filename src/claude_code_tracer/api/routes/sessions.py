"""Session-related API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from claude_code_tracer.api.dependencies import (
    CommonQuery,
    OptionalUser,
    SupabaseServiceDep,
)
from claude_code_tracer.models import (
    SessionDetailResponse,
    SessionListResponse,
    SessionStats,
)

router = APIRouter()


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    supabase: SupabaseServiceDep,
    user: OptionalUser,
    query: CommonQuery,
    status: Optional[str] = Query(None, description="Filter by status"),
    project_path: Optional[str] = Query(None, description="Filter by project path"),
):
    """List sessions with optional filters."""
    # Get user ID if authenticated
    user_id = UUID(user["id"]) if user else None
    
    # Fetch sessions
    sessions = await supabase.list_sessions(
        user_id=user_id,
        status=status,
        limit=query.limit,
        offset=query.offset,
    )
    
    # Get total count
    total = await supabase.get_session_count(user_id=user_id)
    
    return SessionListResponse(
        sessions=sessions,
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get("/stats", response_model=SessionStats)
async def get_session_stats(
    supabase: SupabaseServiceDep,
    user: OptionalUser,
):
    """Get aggregated session statistics."""
    user_id = UUID(user["id"]) if user else None
    
    # This would typically be implemented as a database view or function
    # For now, we'll calculate from the sessions
    sessions = await supabase.list_sessions(user_id=user_id, limit=1000)
    
    stats = SessionStats(
        total_sessions=len(sessions),
        active_sessions=len([s for s in sessions if s.status == "active"]),
        completed_sessions=len([s for s in sessions if s.status == "completed"]),
        error_sessions=len([s for s in sessions if s.status == "error"]),
        total_interactions=sum(s.total_interactions for s in sessions),
        total_cost_usd=sum(s.total_cost_usd for s in sessions),
    )
    
    # Calculate averages
    completed = [s for s in sessions if s.status == "completed" and s.end_time]
    if completed:
        durations = [
            (s.end_time - s.start_time).total_seconds()
            for s in completed
            if s.end_time
        ]
        stats.avg_session_duration_seconds = sum(durations) / len(durations)
        stats.avg_interactions_per_session = (
            sum(s.total_interactions for s in completed) / len(completed)
        )
    
    return stats


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: UUID,
    supabase: SupabaseServiceDep,
    user: OptionalUser,
):
    """Get detailed information about a specific session."""
    # Fetch session
    session = await supabase.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check access permissions
    if user and session.user_id and str(session.user_id) != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Fetch interactions
    interactions = await supabase.list_interactions(session_id)
    
    # Convert to full session model
    full_session = session.model_copy()
    full_session.interactions = interactions
    
    return SessionDetailResponse(
        session=full_session,
        interactions=interactions,
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID,
    supabase: SupabaseServiceDep,
    user: OptionalUser,
):
    """Delete a session and all its data."""
    # Fetch session to check ownership
    session = await supabase.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check access permissions
    if user and session.user_id and str(session.user_id) != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete session (cascades to interactions)
    success = await supabase.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    
    return {"message": "Session deleted successfully"}


@router.get("/by-claude-id/{claude_session_id}")
async def get_session_by_claude_id(
    claude_session_id: str,
    supabase: SupabaseServiceDep,
    user: OptionalUser,
):
    """Get session by Claude session ID."""
    session = await supabase.get_session_by_claude_id(claude_session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check access permissions
    if user and session.user_id and str(session.user_id) != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session