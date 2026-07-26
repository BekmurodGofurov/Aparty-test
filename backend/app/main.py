from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.lifespan import lifespan

from app.domains.users.router import router as users_router
from app.domains.apartments.router import router as apartments_router
from app.domains.orders.router import router as orders_router
from app.domains.media.router import router as media_router
from app.domains.admin.router import router as admin_router

app = FastAPI(
    title="Aparty.uz API", 
    version="1.0.0", 
    redirect_slashes=False, 
    lifespan=lifespan
)

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

_DOMAIN_ROUTERS = [
    (users_router,      "/api/v1",           ["users", "auth"]),
    (apartments_router, "/api/v1/apartments", ["apartments"]),
    (orders_router,     "/api/v1",           ["orders"]),
    (media_router,      "/api/v1/media",     ["media"]),
    (admin_router,      "/api/v1/admin",     ["admin"]),
]

for router, prefix, tags in _DOMAIN_ROUTERS:
    app.include_router(router, prefix=prefix, tags=tags)

@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
