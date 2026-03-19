"""
FastAPI Backend for SwasthyaAI — Offline-First Hospital AI System.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import init_db, SessionLocal
from routers import health
from routers import orchestrator as orchestrator_router
from routers import audit as audit_router
from routers import patients as patients_router
from routers import documents as documents_router
from routers import appointments as appointments_router
from routers import auth as auth_router
from agents import register_all_agents
from services.auth_service import get_current_user, require_admin


def _seed_admin() -> None:
    """Create a default admin user if none exists."""
    from models.user import User
    from services.auth_service import hash_password

    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == "admin@swasthya.local").first()
        if not exists:
            admin = User(
                email="admin@swasthya.local",
                hashed_password=hash_password("Admin@1234"),
                full_name="System Administrator",
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("✓ Default admin created: admin@swasthya.local / Admin@1234")
        else:
            print("✓ Admin user already exists")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"\n🏥 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔌 Offline-first mode: ENABLED")

    init_db()
    _seed_admin()
    register_all_agents()

    print(f"🤖 Agent orchestrator ready\n")
    yield
    print("\n👋 Shutting down gracefully...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Offline-first healthcare AI system with clinical decision support",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public routes (no auth)
app.include_router(health.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")

# Protected routes — authenticated users
app.include_router(
    orchestrator_router.router,
    prefix="/api",
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    patients_router.router,
    prefix="/api",
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    documents_router.router,
    prefix="/api",
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    appointments_router.router,
    prefix="/api",
    dependencies=[Depends(get_current_user)],
)

# Admin-only routes
app.include_router(
    audit_router.router,
    prefix="/api",
    dependencies=[Depends(require_admin)],
)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health",
        "auth": {"login": "/api/auth/login", "register": "/api/auth/register", "me": "/api/auth/me"},
        "orchestrator": {"query": "/api/orchestrator/query", "agents": "/api/orchestrator/agents"},
        "offline_mode": True,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
