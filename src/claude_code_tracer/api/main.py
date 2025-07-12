"""FastAPI application for Claude Code Tracer."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from claude_code_tracer import __version__
from claude_code_tracer.api.routes import sessions, interactions, analytics
from claude_code_tracer.utils.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan management."""
    # Startup
    print("🚀 Starting Claude Code Tracer API...")
    settings = get_settings()
    print(f"Environment: {settings.log_level}")
    print(f"Privacy mode: {settings.privacy_mode}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Claude Code Tracer API...")


# Create FastAPI app
app = FastAPI(
    title="Claude Code Tracer API",
    description="API for tracking and analyzing Claude Code sessions",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
settings = get_settings()
origins = settings.cors_origins.split(",") if hasattr(settings, "cors_origins") else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "privacy_mode": settings.privacy_mode,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Claude Code Tracer API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(
    sessions.router,
    prefix="/api/v1/sessions",
    tags=["Sessions"],
)

app.include_router(
    interactions.router,
    prefix="/api/v1/interactions",
    tags=["Interactions"],
)

app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["Analytics"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": str(exc) if settings.log_level == "DEBUG" else None,
            }
        },
    )