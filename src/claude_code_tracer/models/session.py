"""Session model definitions for Claude Code Tracer."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class SessionBase(BaseModel):
    """Base session model with common fields."""
    
    session_id: str = Field(..., description="Unique session identifier from Claude Code")
    project_path: str = Field(..., description="Absolute path to the project directory")
    user_id: Optional[UUID] = Field(None, description="User ID from Supabase auth")
    status: str = Field(default="active", description="Session status: active, completed, error")
    metadata: Dict = Field(default_factory=dict, description="Additional session metadata")
    
    @field_validator("project_path")
    @classmethod
    def validate_project_path(cls, v: str) -> str:
        """Ensure project path is absolute."""
        if not v.startswith("/"):
            raise ValueError("Project path must be absolute")
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate session status."""
        valid_statuses = {"active", "completed", "error", "timeout"}
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        return v


class SessionCreate(SessionBase):
    """Model for creating a new session."""
    
    start_time: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionUpdate(BaseModel):
    """Model for updating session fields."""
    
    status: Optional[str] = None
    end_time: Optional[datetime] = None
    total_interactions: Optional[int] = None
    total_cost_usd: Optional[float] = None
    metadata: Optional[Dict] = None
    error_message: Optional[str] = None


class SessionInDB(SessionBase):
    """Session model as stored in database."""
    
    id: UUID = Field(default_factory=uuid4, description="Primary key")
    start_time: datetime
    end_time: Optional[datetime] = None
    total_interactions: int = Field(default=0, ge=0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        
        from_attributes = True


class Session(SessionInDB):
    """Full session model with computed fields."""
    
    duration_seconds: Optional[int] = None
    interactions: List["Interaction"] = Field(default_factory=list)
    
    @field_validator("duration_seconds", mode="before")
    @classmethod
    def calculate_duration(cls, v, values):
        """Calculate session duration."""
        if "start_time" in values and "end_time" in values and values["end_time"]:
            duration = values["end_time"] - values["start_time"]
            return int(duration.total_seconds())
        return None


class SessionListResponse(BaseModel):
    """Response model for session list endpoints."""
    
    sessions: List[SessionInDB]
    total: int
    limit: int
    offset: int


class SessionDetailResponse(BaseModel):
    """Response model for session detail endpoints."""
    
    session: Session
    interactions: List["Interaction"]


class SessionStats(BaseModel):
    """Session statistics model."""
    
    total_sessions: int = 0
    active_sessions: int = 0
    completed_sessions: int = 0
    error_sessions: int = 0
    total_interactions: int = 0
    total_cost_usd: float = 0.0
    avg_session_duration_seconds: Optional[float] = None
    avg_interactions_per_session: Optional[float] = None
    
    @field_validator("avg_session_duration_seconds", "avg_interactions_per_session", mode="before")
    @classmethod
    def round_averages(cls, v):
        """Round average values to 2 decimal places."""
        return round(v, 2) if v is not None else None


# Forward reference imports
from claude_code_tracer.models.interaction import Interaction

# Update forward references
Session.model_rebuild()
SessionDetailResponse.model_rebuild()