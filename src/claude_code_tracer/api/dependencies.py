"""Common dependencies for API endpoints."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from claude_code_tracer.services.supabase import SupabaseService, get_supabase_service
from claude_code_tracer.utils.config import Settings, get_settings


# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    supabase: Annotated[SupabaseService, Depends(get_supabase_service)],
) -> dict:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    
    try:
        # Verify JWT token with Supabase
        user = supabase.client.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        return {
            "id": user.user.id,
            "email": user.user.email,
            "metadata": user.user.user_metadata,
        }
    
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


async def get_optional_user(
    authorization: Annotated[Optional[str], Header()] = None,
    supabase: Annotated[SupabaseService, Depends(get_supabase_service)] = None,
) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    try:
        user = supabase.client.auth.get_user(token)
        if user and user.user:
            return {
                "id": user.user.id,
                "email": user.user.email,
                "metadata": user.user.user_metadata,
            }
    except Exception:
        pass
    
    return None


class CommonQueryParams:
    """Common query parameters for list endpoints."""
    
    def __init__(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")
        
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="Sort order must be 'asc' or 'desc'")
        
        self.limit = limit
        self.offset = offset
        self.sort_by = sort_by
        self.sort_order = sort_order


# Dependency aliases
CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalUser = Annotated[Optional[dict], Depends(get_optional_user)]
CommonQuery = Annotated[CommonQueryParams, Depends()]
SupabaseServiceDep = Annotated[SupabaseService, Depends(get_supabase_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]