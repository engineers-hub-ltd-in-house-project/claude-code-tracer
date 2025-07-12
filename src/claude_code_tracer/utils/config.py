"""Configuration management for Claude Code Tracer."""

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: SecretStr = Field(..., description="Supabase anon key")
    supabase_service_role_key: SecretStr = Field(..., description="Supabase service role key")
    
    # Anthropic/Claude Configuration
    anthropic_api_key: SecretStr = Field(..., description="Anthropic API key")
    
    # Application Configuration
    secret_key: SecretStr = Field(
        default_factory=lambda: SecretStr(os.urandom(32).hex()),
        description="Application secret key",
    )
    
    # Privacy Settings
    privacy_mode: Literal["strict", "moderate", "minimal"] = Field(
        default="strict",
        description="Privacy protection level",
    )
    
    # GitHub Integration (Optional)
    github_token: Optional[SecretStr] = Field(None, description="GitHub personal access token")
    github_repo: Optional[str] = Field(None, description="GitHub backup repository")
    
    # Monitoring Settings
    auto_sync_interval: int = Field(default=300, description="Auto-sync interval in seconds")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    
    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_file: Path = Field(
        default=Path("logs/claude-tracer.log"),
        description="Log file path",
    )
    
    # API Server Configuration
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    api_reload: bool = Field(default=False, description="Enable auto-reload for development")
    cors_origins: str = Field(default="*", description="CORS allowed origins")
    
    # Database Configuration
    database_url: Optional[str] = Field(None, description="Override database URL")
    
    # Redis Configuration (for caching)
    redis_url: Optional[str] = Field(None, description="Redis connection URL")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=1000, description="Rate limit requests per hour")
    
    # Export Settings
    export_path: Path = Field(
        default=Path("exports"),
        description="Default export directory",
    )
    
    @field_validator("log_file", "export_path")
    @classmethod
    def ensure_parent_exists(cls, v: Path) -> Path:
        """Ensure parent directory exists for file paths."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        """Validate Supabase URL format."""
        if not v.startswith(("https://", "http://")):
            raise ValueError("Supabase URL must start with https:// or http://")
        if not v.endswith(".supabase.co"):
            raise ValueError("Invalid Supabase URL format")
        return v.rstrip("/")
    
    @property
    def supabase_headers(self) -> dict:
        """Get headers for Supabase requests."""
        return {
            "apikey": self.supabase_key.get_secret_value(),
            "Authorization": f"Bearer {self.supabase_key.get_secret_value()}",
        }
    
    @property
    def supabase_service_headers(self) -> dict:
        """Get service role headers for Supabase admin requests."""
        return {
            "apikey": self.supabase_service_role_key.get_secret_value(),
            "Authorization": f"Bearer {self.supabase_service_role_key.get_secret_value()}",
        }
    
    def get_privacy_patterns_path(self) -> Path:
        """Get path to privacy patterns configuration file."""
        return Path("config/privacy.yml")
    
    def is_github_enabled(self) -> bool:
        """Check if GitHub integration is enabled."""
        return self.github_token is not None and self.github_repo is not None


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings instance (mainly for testing)."""
    global _settings
    _settings = None