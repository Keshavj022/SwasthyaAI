"""
FastAPI Backend for Offline-First Hospital AI System.

This server provides:
- Local SQLite database (offline-first)
- Health check endpoints
- Future: Agent orchestration API
- Future: Medical AI inference endpoints

Designed to run on local hospital servers or edge devices.
No cloud dependencies required for core functionality.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import init_db
from routers import health
from routers import orchestrator as orchestrator_router
from routers import audit as audit_router
from routers import patients as patients_router
from routers import documents as documents_router
from agents import register_all_agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database and registers agents on startup.
    """
    print(f"\n🏥 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔌 Offline-first mode: ENABLED")

    # Initialize database
    init_db()

    # Register all agents with orchestrator
    register_all_agents()

    print(f"🤖 Agent orchestrator ready\n")

    yield

    # Cleanup on shutdown
    print("\n👋 Shutting down gracefully...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Offline-first healthcare AI system with clinical decision support",
    lifespan=lifespan,
)

# CORS middleware - allow Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(orchestrator_router.router, prefix="/api")
app.include_router(audit_router.router, prefix="/api")
app.include_router(patients_router.router, prefix="/api")
app.include_router(documents_router.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health",
        "orchestrator": {
            "query": "/api/orchestrator/query",
            "agents": "/api/orchestrator/agents",
            "health": "/api/orchestrator/health"
        },
        "offline_mode": True,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,  # Auto-reload on code changes (development only)
    )
