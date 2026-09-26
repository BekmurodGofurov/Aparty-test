"""Order Service Main Application Entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.rabbitmq import close_rabbitmq, init_rabbitmq
from app.routers.bookings import router as bookings_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(settings.service_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_rabbitmq()
    yield
    await close_rabbitmq()


app = FastAPI(
    title="Aparty Order Service",
    version="1.0.0",
    description="Booking requests for listings",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bookings_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": settings.service_name}
