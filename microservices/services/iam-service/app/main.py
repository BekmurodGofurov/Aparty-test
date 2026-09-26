"""IAM Service — FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.redis_client import close_redis, init_redis
from app.constants import API_PREFIX
from app.routers import auth, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for IAM service."""
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("IAM Service starting up...")
    await init_db()
    await init_redis()
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
        "Handles Telegram login, user profiles and JWT issuance."
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
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Meta"], summary="Service health check")
async def health() -> dict:
    return {"status": "ok", "service": "iam-service"}
