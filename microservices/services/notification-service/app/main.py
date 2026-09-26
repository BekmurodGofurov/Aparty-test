"""Notification Service Main Application Entrypoint."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.consumers import run_consumer
from app.database import init_db
from app.rabbitmq import close_rabbitmq, init_rabbitmq
from app.routers.notifications import router as notifications_router

logging.basicConfig(level=logging.INFO)
# httpx logs the full request URL at INFO level, and the Telegram bot token is part of that URL.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(settings.service_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_rabbitmq()
    consumer_task = asyncio.create_task(run_consumer())
    yield
    consumer_task.cancel()
    await close_rabbitmq()


app = FastAPI(
    title="Aparty Notification Service",
    version="1.0.0",
    description="Site notifications and Telegram messages, created from booking and listing events",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notifications_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": settings.service_name}
