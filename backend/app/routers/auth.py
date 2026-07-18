"""Authentication router.

Login flow (Authenticator App model):
──────────────────────────────────────
                 Bot (pure client)          React (pure client)
                        │                          │
  user types /login     │                          │
  ─────────────────────>│                          │
                        │  POST /bot/login-code    │
                        │─────────────────────────>│  (backend)
                        │  { code: "482031" }      │
                        │<─────────────────────────│
  bot shows code        │                          │
  user goes to website  │                          │
                        │      POST /login         │
                        │   { code: "482031" }     │
                        │<─────────────────────────│
                        │   { access_token }       │
                        │─────────────────────────>│

The backend NEVER contacts Telegram.  Both the Bot and React are pure HTTP
clients that hit this API — exactly the same relationship.
"""
import logging
import os
from typing import Optional

from dotenv import dotenv_values
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import BACKEND_DIR, settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas.auth import (
    AdminLoginRequest,
    AuthSuccessResponse,
    BotLoginCodeRequest,
    BotLoginCodeResponse,
    CodeLoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserOut
from app.utils.login_code_store import generate_login_code, verify_and_consume_code
from app.utils.security import create_token
from database.operations.insert import users as insert_users
from database.operations.select import users as select_users

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_minutes * 60,
    )


# ─── Registration (Bot → Backend) ─────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
    """Register a new user.

    Called by the Telegram bot after the user completes the FSM flow
    (Language → Name → Role → Phone). The bot sends the Telegram ID as `id`,
    which is stored directly as the primary key — no separate telegram_id
    column, no password.

    Because the phone number was verified via Telegram's native
    contact-sharing mechanism, is_verified is set to True immediately.
    """
    # Reject if Telegram ID already registered
    existing = await select_users.get_by_id(db, payload.id)
    if existing is not None:
        raise HTTPException(status_code=400, detail="User with this Telegram ID already exists")

    if await select_users.get_by_phone(db, payload.phone) is not None:
        raise HTTPException(status_code=400, detail="Phone number is already registered")

    if payload.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Cannot register with admin role")

    user = User(
        id=payload.id,          # Telegram ID IS the PK
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        is_verified=True,       # Verified by Telegram contact-sharing
    )
    return await insert_users.create(db, user)


# ─── Bot: Generate Login Code ──────────────────────────────────────────────────

@router.post("/bot/login-code", response_model=BotLoginCodeResponse)
async def bot_generate_login_code(
    payload: BotLoginCodeRequest,
    db: AsyncSession = Depends(get_db),
) -> BotLoginCodeResponse:
    """Generate a single-use 6-digit login code for a registered user.

    Called by the Telegram bot when the user sends the /login command.
    The bot then displays the code to the user, who types it on the website.

    Security guarantees:
    - Code is generated with secrets.randbelow() (OS CSPRNG).
    - TTL is 120 seconds (2 minutes, monotonic clock).
    - Single-use: deleted on first successful verification.
    - Backend never sends the code anywhere — the bot is the display layer.

    Returns 404 if the Telegram ID is not registered.
    """
    user = await select_users.get_by_id(db, payload.id)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Bu Telegram akkaunt ro'yxatdan o'tmagan. Iltimos, /start bilan ro'yxatdan o'ting.",
        )

    code = generate_login_code(user.id)
    logger.info("Login code generated for user_id=%s", user.id)
    return BotLoginCodeResponse(code=code)


# ─── Website Login (React → Backend, code only) ───────────────────────────────

@router.post("/login", response_model=AuthSuccessResponse)
async def login(
    payload: CodeLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccessResponse:
    """Validate a 6-digit login code and issue JWT tokens.

    The React frontend login page has a single 6-digit code input field.
    The user gets the code from the Telegram bot (/login command).

    Strict rules:
    - Missing code   → 400 Bad Request.
    - Expired code   → 400 Bad Request (TTL = 2 minutes).
    - Already used   → 400 Bad Request (single-use).
    - Valid code     → delete from cache, issue access + refresh tokens.
    """
    user_id = verify_and_consume_code(payload.code)
    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Kod noto'g'ri yoki muddati o'tgan. Iltimos, botdan yangi kod oling.",
        )

    user = await select_users.get_by_id(db, user_id)
    if user is None:
        # Should never happen (code was generated for a valid user_id)
        logger.error("Login code valid but user_id=%s not found in DB", user_id)
        raise HTTPException(status_code=404, detail="User not found")

    access_token = create_token(str(user.id), expires_minutes=settings.access_token_expire_minutes)
    refresh_token = create_token(str(user.id), expires_minutes=settings.refresh_token_expire_minutes)
    set_refresh_cookie(response, refresh_token)

    logger.info("Login successful for user_id=%s", user.id)
    return AuthSuccessResponse(access_token=access_token)


# ─── Root Admin Login (Bypasses Database) ──────────────────────────────────────

@router.post("/admin-login", response_model=AuthSuccessResponse)
async def admin_login(
    request: Request,
    response: Response,
    payload: Optional[AdminLoginRequest] = Body(default=None),
) -> AuthSuccessResponse:
    """Root Admin login endpoint. Bypasses database tables entirely.

    Accepts JSON ({'username': '...', 'password': '...'}) or OAuth2 form data.
    Directly compares credentials against environment variables ADMIN_USERNAME and ADMIN_PASSWORD.
    If successful, issues a JWT token with sub='admin' and role='admin'.
    """
    username = payload.username if payload else None
    password = payload.password if payload else None

    if not username or not password:
        try:
            form = await request.form()
            username = username or form.get("username")
            password = password or form.get("password")
        except Exception:
            pass

    # Dynamically read .env first so any updates without uvicorn restart take immediate effect
    env_dict = dotenv_values(BACKEND_DIR / ".env")
    expected_username = env_dict.get("ADMIN_USERNAME") or os.getenv("ADMIN_USERNAME") or settings.admin_username
    expected_password = env_dict.get("ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD") or settings.admin_password

    if not username or not password or username != expected_username or password != expected_password:
        logger.warning("Failed root admin login attempt for username=%s", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_token(
        subject="admin",
        expires_minutes=settings.access_token_expire_minutes,
        extra_claims={"role": "admin"},
    )
    refresh_token = create_token(
        subject="admin",
        expires_minutes=settings.refresh_token_expire_minutes,
        extra_claims={"role": "admin"},
    )
    set_refresh_cookie(response, refresh_token)

    logger.info("Root Admin logged in successfully via environment credentials")
    return AuthSuccessResponse(access_token=access_token)


# ─── Token Refresh ─────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    payload: Optional[RefreshRequest] = Body(default=None),
) -> TokenResponse:
    """Refresh access token using the httpOnly refresh cookie."""
    token = request.cookies.get("refresh_token") or (payload.refresh_token if payload else None)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        data = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = data.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    return TokenResponse(
        message="Access token refreshed",
        access_token=create_token(str(user_id), expires_minutes=settings.access_token_expire_minutes),
    )


# ─── Logout ───────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(response: Response) -> dict[str, object]:
    """Logout user — clear the refresh token cookie."""
    response.delete_cookie("refresh_token")
    return {"success": True, "message": "Logged out successfully"}


# ─── Current User ─────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Get the currently authenticated user."""
    return current_user


# ─── Bot: Check User Exists ───────────────────────────────────────────────────

@router.get("/bot/check/{telegram_id}")
async def check_user_by_telegram_id(telegram_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    """Check if a user is registered by their Telegram ID.

    Called by the bot's /start handler to determine whether to show
    the registration flow or the welcome-back message.

    Since users.id IS the Telegram ID (BigInteger PK), this is simply
    a get_by_id lookup.
    """
    user = await select_users.get_by_id(db, telegram_id)

    if user:
        return {
            "success": True,
            "data": {
                "exists": True,
                "id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "is_verified": user.is_verified,
            },
        }

    return {"success": True, "data": {"exists": False}}


@router.get("/bot/check/phone/{phone}")
async def check_user_by_phone(phone: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Check if a user exists by phone number (used by the bot to prevent duplicates)."""
    user = await select_users.get_by_phone(db, phone)

    if user:
        return {
            "success": True,
            "data": {
                "exists": True,
                "id": user.id,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "is_verified": user.is_verified,
            },
        }

    return {"success": True, "data": {"exists": False}}
