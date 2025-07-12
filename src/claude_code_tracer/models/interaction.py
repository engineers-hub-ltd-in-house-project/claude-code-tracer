"""Interaction model definitions for Claude Code Tracer."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ToolUsage(BaseModel):
    """Model for tool usage information."""
    
    tool_name: str = Field(..., description="Name of the tool used")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result_summary: Optional[str] = None
    execution_time_ms: Optional[int] = Field(None, ge=0)
    error: Optional[str] = None


class PerformanceMetrics(BaseModel):
    """Performance metrics for an interaction."""
    
    response_time_ms: int = Field(..., ge=0, description="Total response time in milliseconds")
    tokens_used: Dict[str, int] = Field(
        default_factory=lambda: {"prompt": 0, "completion": 0, "total": 0}
    )
    model: str = Field(default="claude-3-sonnet", description="Model used")
    cost_usd: float = Field(default=0.0, ge=0.0, description="Cost in USD")
    
    @field_validator("tokens_used")
    @classmethod
    def validate_tokens(cls, v: Dict[str, int]) -> Dict[str, int]:
        """Ensure token counts are consistent."""
        if v.get("total", 0) != v.get("prompt", 0) + v.get("completion", 0):
            v["total"] = v.get("prompt", 0) + v.get("completion", 0)
        return v


class ContextAnalysis(BaseModel):
    """Analysis of the interaction context."""
    
    intent_type: Optional[str] = Field(
        None, 
        description="Detected intent: code_generation, debugging, refactoring, etc."
    )
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    complexity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    topics: List[str] = Field(default_factory=list)


class PrivacyStatus(BaseModel):
    """Privacy scan results for an interaction."""
    
    scanned: bool = Field(default=False)
    patterns_detected: List[str] = Field(default_factory=list)
    masking_applied: bool = Field(default=False)
    scan_timestamp: Optional[datetime] = None


class InteractionBase(BaseModel):
    """Base interaction model with common fields."""
    
    session_id: UUID = Field(..., description="Reference to parent session")
    message_type: str = Field(..., description="Type: user, assistant, system")
    sequence_number: int = Field(..., ge=0, description="Order in the conversation")
    
    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v: str) -> str:
        """Validate message type."""
        valid_types = {"user", "assistant", "system"}
        if v not in valid_types:
            raise ValueError(f"Invalid message type. Must be one of: {valid_types}")
        return v


class InteractionCreate(InteractionBase):
    """Model for creating a new interaction."""
    
    user_prompt: Optional[str] = None
    claude_response: Optional[str] = None
    tools_used: List[ToolUsage] = Field(default_factory=list)
    performance_metrics: Optional[PerformanceMetrics] = None
    context_analysis: Optional[ContextAnalysis] = None
    privacy_status: PrivacyStatus = Field(default_factory=PrivacyStatus)
    raw_message: Optional[Dict[str, Any]] = Field(None, description="Original message data")


class InteractionUpdate(BaseModel):
    """Model for updating interaction fields."""
    
    claude_response: Optional[str] = None
    tools_used: Optional[List[ToolUsage]] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    context_analysis: Optional[ContextAnalysis] = None
    privacy_status: Optional[PrivacyStatus] = None
    error_message: Optional[str] = None


class InteractionInDB(InteractionBase):
    """Interaction model as stored in database."""
    
    id: UUID = Field(default_factory=uuid4, description="Primary key")
    user_prompt: Optional[str] = None
    claude_response: Optional[str] = None
    tools_used: List[ToolUsage] = Field(default_factory=list)
    performance_metrics: Optional[PerformanceMetrics] = None
    context_analysis: Optional[ContextAnalysis] = None
    privacy_status: PrivacyStatus = Field(default_factory=PrivacyStatus)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic configuration."""
        
        from_attributes = True


class Interaction(InteractionInDB):
    """Full interaction model with additional computed fields."""
    
    @property
    def is_error(self) -> bool:
        """Check if interaction contains an error."""
        return self.error_message is not None
    
    @property
    def has_tool_usage(self) -> bool:
        """Check if interaction used any tools."""
        return len(self.tools_used) > 0
    
    @property
    def total_tool_execution_time_ms(self) -> int:
        """Calculate total tool execution time."""
        return sum(
            tool.execution_time_ms or 0 
            for tool in self.tools_used
        )


class InteractionSearchRequest(BaseModel):
    """Request model for searching interactions."""
    
    query: Optional[str] = Field(None, description="Search query")
    session_ids: Optional[List[UUID]] = None
    message_types: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    has_tools: Optional[bool] = None
    intent_types: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class InteractionSearchResponse(BaseModel):
    """Response model for interaction search."""
    
    interactions: List[InteractionInDB]
    total_results: int
    query: Optional[str] = None
    relevance_scores: Optional[Dict[UUID, float]] = None