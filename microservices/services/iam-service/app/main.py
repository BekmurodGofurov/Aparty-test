"""IAM Service — FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.redis_client import close_redis, init_redis
from app.routers import auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for IAM service."""
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("IAM Service starting up...")
    await init_db()          # Create tables if they don't exist (dev mode)
    await init_redis()       # Open Redis connection pool
    logger.info("IAM Service ready.")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("IAM Service shutting down...")
    await close_redis()
    logger.info("IAM Service stopped.")


app = FastAPI(
    title="Aparty — IAM Service",
    description=(
        "Identity & Access Management microservice.\n\n"
        "Handles user registration, OTP-based authentication (via Telegram bot), "
        "and JWT issuance."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Meta"], summary="Service health check")
async def health() -> dict:
    return {"status": "ok", "service": "iam-service"}
