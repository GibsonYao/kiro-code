"""FastAPI application entry point for AI Family Butler (小灶AI家庭管家)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.deps import engine
from app.core.middleware import (
    FamilyDataIsolationMiddleware,
    ResponseTimeMiddleware,
    SecurityHeadersMiddleware,
)
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables on startup (demo mode)."""
    # Import all models so Base.metadata knows about them
    import app.models  # noqa: F401

    # Auto-create tables in demo mode (both SQLite and PostgreSQL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-native family management application",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Response time monitoring middleware
app.add_middleware(ResponseTimeMiddleware)

# Family data isolation middleware
app.add_middleware(FamilyDataIsolationMiddleware)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Include API v1 router
app.include_router(api_router, prefix="/api/v1")
