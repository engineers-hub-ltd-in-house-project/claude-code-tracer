"""Supabase service for database operations and real-time sync."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from claude_code_tracer.models import (
    Interaction,
    InteractionCreate,
    InteractionInDB,
    InteractionUpdate,
    Session,
    SessionCreate,
    SessionInDB,
    SessionUpdate,
)
from claude_code_tracer.utils.config import get_settings


class SupabaseService:
    """Service class for Supabase operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        settings = get_settings()
        options = ClientOptions()
        options.auto_refresh_token = True
        options.persist_session = True
        
        self.client: Client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_key.get_secret_value(),
            options=options,
        )
        
        # Use service role client for admin operations
        self.admin_client: Client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key.get_secret_value(),
            options=options,
        )
    
    # ========== Session Operations ==========
    
    async def create_session(self, session: SessionCreate) -> SessionInDB:
        """Create a new session in the database."""
        data = session.model_dump(mode='json')
        data["id"] = str(UUID(int=0))  # Let DB generate UUID
        
        response = self.client.table("claude_sessions").insert(data).execute()
        
        if response.data:
            return SessionInDB(**response.data[0])
        raise Exception("Failed to create session")
    
    async def get_session(self, session_id: UUID) -> Optional[SessionInDB]:
        """Get a session by ID."""
        response = self.client.table("claude_sessions").select("*").eq("id", str(session_id)).single().execute()
        
        if response.data:
            return SessionInDB(**response.data)
        return None
    
    async def get_session_by_claude_id(self, claude_session_id: str) -> Optional[SessionInDB]:
        """Get a session by Claude session ID."""
        response = self.client.table("claude_sessions").select("*").eq("session_id", claude_session_id).single().execute()
        
        if response.data:
            return SessionInDB(**response.data)
        return None
    
    async def list_sessions(
        self,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SessionInDB]:
        """List sessions with optional filters."""
        query = self.client.table("claude_sessions").select("*")
        
        if user_id:
            query = query.eq("user_id", str(user_id))
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        response = query.execute()
        
        return [SessionInDB(**row) for row in response.data]
    
    async def update_session(self, session_id: UUID, update: SessionUpdate) -> SessionInDB:
        """Update a session."""
        data = update.model_dump(exclude_unset=True)
        data["updated_at"] = datetime.utcnow().isoformat()
        
        response = self.client.table("claude_sessions").update(data).eq("id", str(session_id)).execute()
        
        if response.data:
            return SessionInDB(**response.data[0])
        raise Exception("Failed to update session")
    
    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a session and all its interactions."""
        # Delete interactions first (cascade)
        self.client.table("claude_interactions").delete().eq("session_id", str(session_id)).execute()
        
        # Delete session
        response = self.client.table("claude_sessions").delete().eq("id", str(session_id)).execute()
        
        return len(response.data) > 0
    
    # ========== Interaction Operations ==========
    
    async def create_interaction(self, interaction: InteractionCreate) -> InteractionInDB:
        """Create a new interaction."""
        data = interaction.model_dump(mode="json")
        data["id"] = str(UUID(int=0))  # Let DB generate UUID
        data["session_id"] = str(interaction.session_id)
        
        # Convert complex objects to JSON strings
        if data.get("tools_used"):
            data["tools_used"] = json.dumps(data["tools_used"])
        if data.get("performance_metrics"):
            data["performance_metrics"] = json.dumps(data["performance_metrics"])
        if data.get("context_analysis"):
            data["context_analysis"] = json.dumps(data["context_analysis"])
        if data.get("privacy_status"):
            data["privacy_status"] = json.dumps(data["privacy_status"])
        
        response = self.client.table("claude_interactions").insert(data).execute()
        
        if response.data:
            return self._parse_interaction(response.data[0])
        raise Exception("Failed to create interaction")
    
    async def get_interaction(self, interaction_id: UUID) -> Optional[InteractionInDB]:
        """Get an interaction by ID."""
        response = self.client.table("claude_interactions").select("*").eq("id", str(interaction_id)).single().execute()
        
        if response.data:
            return self._parse_interaction(response.data)
        return None
    
    async def list_interactions(
        self,
        session_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InteractionInDB]:
        """List interactions for a session."""
        response = (
            self.client.table("claude_interactions")
            .select("*")
            .eq("session_id", str(session_id))
            .order("sequence_number", desc=False)
            .range(offset, offset + limit - 1)
            .execute()
        )
        
        return [self._parse_interaction(row) for row in response.data]
    
    async def update_interaction(
        self,
        interaction_id: UUID,
        update: InteractionUpdate,
    ) -> InteractionInDB:
        """Update an interaction."""
        data = update.model_dump(exclude_unset=True, mode="json")
        
        # Convert complex objects to JSON strings
        for field in ["tools_used", "performance_metrics", "context_analysis", "privacy_status"]:
            if field in data and data[field] is not None:
                data[field] = json.dumps(data[field])
        
        response = self.client.table("claude_interactions").update(data).eq("id", str(interaction_id)).execute()
        
        if response.data:
            return self._parse_interaction(response.data[0])
        raise Exception("Failed to update interaction")
    
    async def search_interactions(
        self,
        query: str,
        session_ids: Optional[List[UUID]] = None,
        limit: int = 20,
    ) -> List[InteractionInDB]:
        """Search interactions by content."""
        search_query = self.client.table("claude_interactions").select("*")
        
        # Text search in user_prompt and claude_response
        search_query = search_query.or_(
            f"user_prompt.ilike.%{query}%,claude_response.ilike.%{query}%"
        )
        
        if session_ids:
            session_id_strs = [str(sid) for sid in session_ids]
            search_query = search_query.in_("session_id", session_id_strs)
        
        response = search_query.order("created_at", desc=True).limit(limit).execute()
        
        return [self._parse_interaction(row) for row in response.data]
    
    # ========== Real-time Operations ==========
    
    def subscribe_to_sessions(self, user_id: Optional[UUID] = None) -> Any:
        """Subscribe to real-time session updates."""
        channel = self.client.channel("sessions")
        
        # Subscribe to all session changes
        if user_id:
            channel = channel.on(
                "postgres_changes",
                callback=lambda payload: print(f"Session change: {payload}"),
                filter=f"user_id=eq.{user_id}",
                schema="public",
                table="claude_sessions",
            )
        else:
            channel = channel.on(
                "postgres_changes",
                callback=lambda payload: print(f"Session change: {payload}"),
                schema="public",
                table="claude_sessions",
            )
        
        channel.subscribe()
        return channel
    
    def subscribe_to_interactions(self, session_id: UUID) -> Any:
        """Subscribe to real-time interaction updates for a session."""
        channel = self.client.channel(f"interactions_{session_id}")
        
        channel = channel.on(
            "postgres_changes",
            callback=lambda payload: print(f"Interaction change: {payload}"),
            filter=f"session_id=eq.{session_id}",
            schema="public",
            table="claude_interactions",
        )
        
        channel.subscribe()
        return channel
    
    # ========== Utility Methods ==========
    
    def _parse_interaction(self, data: Dict[str, Any]) -> InteractionInDB:
        """Parse interaction data from database."""
        # Parse JSON fields
        for field in ["tools_used", "performance_metrics", "context_analysis", "privacy_status"]:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except json.JSONDecodeError:
                    data[field] = None
        
        return InteractionInDB(**data)
    
    async def get_session_count(self, user_id: Optional[UUID] = None) -> int:
        """Get total session count."""
        query = self.client.table("claude_sessions").select("id", count="exact")
        
        if user_id:
            query = query.eq("user_id", str(user_id))
        
        response = query.execute()
        return response.count or 0
    
    async def get_interaction_count(self, session_id: Optional[UUID] = None) -> int:
        """Get total interaction count."""
        query = self.client.table("claude_interactions").select("id", count="exact")
        
        if session_id:
            query = query.eq("session_id", str(session_id))
        
        response = query.execute()
        return response.count or 0


# Singleton instance
_supabase_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """Get or create Supabase service instance."""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service