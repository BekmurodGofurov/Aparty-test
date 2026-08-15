"""Catalog Service Main Application Entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.rabbitmq import close_rabbitmq, init_rabbitmq
from app.routers.bookings import router as bookings_router
from app.routers.listings import router as listings_router
from app.routers.media import router as media_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("catalog-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Catalog Service database...")
    await init_db()
    logger.info("Initializing RabbitMQ connection...")
    await init_rabbitmq()
    yield
    logger.info("Shutting down Catalog Service...")
    await close_rabbitmq()


app = FastAPI(
    title="Aparty Catalog Service",
    version="1.0.0",
    description="Unified Catalog Service for real estate listings, ImgBB media uploads, and bookings/orders",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings_router)
app.include_router(media_router)
app.include_router(bookings_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": settings.service_name,
    }
