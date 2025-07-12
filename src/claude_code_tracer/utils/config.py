"""
Configuration management using pydantic-settings
"""

from functools import lru_cache
from typing import Optional, List
from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class PrivacyMode(str, Enum):
    """Privacy protection levels"""
    STRICT = "strict"
    MODERATE = "moderate"
    MINIMAL = "minimal"


class Environment(str, Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """Application settings"""
    
    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon key")
    supabase_service_role_key: str = Field(..., description="Supabase service role key")
    
    # Claude/Anthropic Configuration
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    
    # GitHub Integration (Optional)
    github_token: Optional[str] = Field(None, description="GitHub personal access token")
    github_repo: Optional[str] = Field(None, description="GitHub repository for backups")
    github_branch: str = Field("main", description="GitHub branch")
    
    # Application Configuration
    log_level: str = Field("INFO", description="Logging level")
    privacy_mode: PrivacyMode = Field(PrivacyMode.STRICT, description="Privacy protection mode")
    auto_sync_interval: int = Field(300, description="Auto sync interval in seconds")
    enable_realtime: bool = Field(True, description="Enable real-time monitoring")
    
    # API Server Configuration
    api_host: str = Field("0.0.0.0", description="API server host")
    api_port: int = Field(8000, description="API server port")
    api_reload: bool = Field(False, description="Enable auto-reload")
    
    # Session Monitoring
    max_concurrent_sessions: int = Field(10, description="Maximum concurrent sessions to monitor")
    session_timeout: int = Field(3600, description="Session timeout in seconds")
    
    # Database Configuration
    db_pool_min: int = Field(2, description="Minimum database connections")
    db_pool_max: int = Field(10, description="Maximum database connections")
    
    # Security
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    cors_origins: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )
    
    # Monitoring & Observability
    enable_tracing: bool = Field(False, description="Enable OpenTelemetry tracing")
    otel_exporter_otlp_endpoint: Optional[str] = Field(None, description="OTLP endpoint")
    enable_metrics: bool = Field(True, description="Enable Prometheus metrics")
    metrics_port: int = Field(9090, description="Metrics server port")
    
    # Feature Flags
    enable_experimental_features: bool = Field(False, description="Enable experimental features")
    enable_ai_analytics: bool = Field(True, description="Enable AI-powered analytics")
    enable_auto_issues: bool = Field(False, description="Enable automatic issue creation")
    
    # External Services
    redis_url: Optional[str] = Field("redis://localhost:6379/0", description="Redis URL")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    
    # Development Settings
    debug: bool = Field(False, description="Enable debug mode")
    environment: Environment = Field(Environment.PRODUCTION, description="Environment")
    log_sql_queries: bool = Field(False, description="Log SQL queries")
    mock_claude_sdk: bool = Field(False, description="Mock Claude SDK for testing")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.environment == Environment.TESTING


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()