import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.routers import admin, ai, auth, listings, notifications, payments, rentals, reviews, subscriptions, upload, users, favorites
from app.tasks.expire_premium import premium_expiry_loop


@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.db_migrations import run_migrations

    await asyncio.to_thread(run_migrations)

    task = asyncio.create_task(premium_expiry_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="Aparty.uz API", version="0.2.0", redirect_slashes=False, lifespan=lifespan)

import os
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(TimeoutError)
async def database_timeout_handler(_: Request, __: TimeoutError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Database connection timed out. Please retry in a moment."},
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_: Request, __: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is temporarily unavailable. Please retry in a moment."},
    )

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(listings.router, prefix="/api/v1/listings", tags=["listings"])
app.include_router(rentals.router, prefix="/api/v1/rentals", tags=["rentals"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["reviews"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(favorites.router, prefix="/api/v1/favorites", tags=["favorites"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])


@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
