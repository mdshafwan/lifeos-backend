"""
LifeOS Backend — Main FastAPI Application Entry Point

This is where everything comes together:
- App initialization
- Middleware setup
- Router registration
- Event handlers (startup/shutdown)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from loguru import logger
import sys
import os

from app.config import settings
from app.database import check_db_connection

from app.routers import (
    tasks, projects, habits, goals, notes, journal,
    calendar, health, finance, contacts, ideas,
    wiki, learning, business, vision_board, documents,
    gamification,ai_coach,  
)

# ── Configure Loguru ─────────────────────────────────────────────
# Remove default logger and add our custom one
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO",
    colorize=True,
)
logger.add(
    "logs/lifeos_{time:YYYY-MM-DD}.log",
    rotation="1 day",       # New file every day
    retention="30 days",    # Keep logs for 30 days
    compression="zip",      # Compress old logs
    level="INFO",
)


# ── Lifespan Handler ─────────────────────────────────────────────
# Modern FastAPI way to handle startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")

    # Check database connection
    if check_db_connection():
        logger.info("✅ Database connection: OK")
    else:
        logger.error("❌ Database connection: FAILED")
        # Don't crash the app — let health endpoint report it

    # Create upload directories if they don't exist
    os.makedirs(f"{settings.UPLOAD_DIR}/documents", exist_ok=True)
    os.makedirs(f"{settings.UPLOAD_DIR}/avatars", exist_ok=True)
    logger.info("✅ Upload directories: OK")

    logger.info(f"📡 Server running at http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📚 API Docs at http://{settings.HOST}:{settings.PORT}/docs")

    yield  # App runs here

    # ── SHUTDOWN ──
    logger.info("👋 Shutting down LifeOS Backend...")


# ── Create FastAPI App ───────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## LifeOS Backend API 🧠

A comprehensive personal life management system backend.

### Features:
- 🔐 **Auth** — JWT-based authentication
- ✅ **Tasks** — Full task management with priorities
- 🎯 **Goals** — Goal tracking with milestones
- 💪 **Habits** — Habit tracking with streaks
- 📓 **Journal** — Daily journaling with mood tracking
- 💰 **Finance** — Income & expense tracking
- 🤖 **AI Coach** — Powered by Ollama (local LLM)
- 🏆 **Gamification** — XP, levels, achievements
- 📊 **Analytics** — Insights & aggregations
    """,
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc UI
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── CORS Middleware ──────────────────────────────────────────────
# WHY? Your React app is on localhost:5173, backend on :8000
# Browsers block cross-origin requests by default — CORS allows it
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,         # Allow cookies & auth headers
    allow_methods=["*"],            # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],            # Authorization, Content-Type, etc.
)


# ── Static Files (for uploads) ───────────────────────────────────
app.mount(
    "/uploads",
    StaticFiles(directory=settings.UPLOAD_DIR),
    name="uploads"
)


# ── Import & Register Routers ────────────────────────────────────
# We'll uncomment these as we build each phase

# Phase 3 — Auth
from app.routers import auth

# Phase 4 — Core APIs (uncomment as we build)
# from app.routers import (
#     tasks, habits, goals, notes, journal,
#     health, finance, contacts, projects,
#     calendar, ideas, wiki, learning,
#     business, vision_board, documents,
# )

# Phase 5 — Gamification
# from app.routers import gamification

# Phase 6 — AI Coach
# from app.routers import ai_coach

# Phase 8 — Analytics
# from app.routers import analytics


# ── Mount Routers ────────────────────────────────────────────────
API_PREFIX = "/api"

app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["🔐 Authentication"])
app.include_router(tasks.router, prefix=f"{API_PREFIX}/tasks", tags=["✅ Tasks"])
app.include_router(projects.router,    prefix=f"{API_PREFIX}/projects",    tags=["📁 Projects"])
app.include_router(habits.router,      prefix=f"{API_PREFIX}/habits",      tags=["💪 Habits"])
app.include_router(goals.router,       prefix=f"{API_PREFIX}/goals",       tags=["🎯 Goals"])
app.include_router(notes.router,       prefix=f"{API_PREFIX}/notes",       tags=["📝 Notes"])
app.include_router(journal.router,     prefix=f"{API_PREFIX}/journal",     tags=["📓 Journal"])
app.include_router(calendar.router,    prefix=f"{API_PREFIX}/calendar",    tags=["📅 Calendar"])
app.include_router(health.router,      prefix=f"{API_PREFIX}/health",      tags=["❤️ Health"])
app.include_router(finance.router,     prefix=f"{API_PREFIX}/finance",     tags=["💰 Finance"])
app.include_router(contacts.router,               prefix=f"{API_PREFIX}/contacts",      tags=["👥 CRM"])
app.include_router(contacts.interactions_router,  prefix=f"{API_PREFIX}/interactions",  tags=["📞 Interactions"])
app.include_router(ideas.router,       prefix=f"{API_PREFIX}/ideas",       tags=["💡 Ideas"])
app.include_router(wiki.router,        prefix=f"{API_PREFIX}/wiki",        tags=["📖 Wiki"])
app.include_router(learning.router,    prefix=f"{API_PREFIX}/learning",    tags=["🎓 Learning"])
app.include_router(business.router,           prefix=f"{API_PREFIX}/business",  tags=["💼 Business Ventures"])
app.include_router(business.clients_router,   prefix=f"{API_PREFIX}/clients",   tags=["👥 Clients"])
app.include_router(business.invoices_router,  prefix=f"{API_PREFIX}/invoices",  tags=["🧾 Invoices"])
app.include_router(business.expenses_router,  prefix=f"{API_PREFIX}/business-expenses", tags=["💸 Business Expenses"])
app.include_router(vision_board.router,prefix=f"{API_PREFIX}/vision-board",tags=["🌟 Vision Board"])
app.include_router(documents.router,   prefix=f"{API_PREFIX}/documents",   tags=["📄 Documents"])
app.include_router(gamification.router,prefix=f"{API_PREFIX}/gamification",tags=["🏆 Gamification"])
app.include_router(ai_coach.router,    prefix=f"{API_PREFIX}/ai",          tags=["🤖 AI Coach"])

# We'll add these in Phase 4:
# app.include_router(analytics.router,   prefix=f"{API_PREFIX}/analytics",   tags=["📊 Analytics"])


# ── Root Endpoints ───────────────────────────────────────────────
@app.get("/", tags=["🏠 Root"])
async def root():
    """Welcome endpoint — confirms the API is running."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API! 🚀",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["🏠 Root"])
async def health_check():
    """
    Health check endpoint.
    Use this to verify the server + database are working.
    """
    db_healthy = check_db_connection()
    return {
        "status": "healthy" if db_healthy else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected" if db_healthy else "disconnected",
        "environment": settings.ENVIRONMENT,
    }