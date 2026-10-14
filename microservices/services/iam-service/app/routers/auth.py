"""IAM authentication router: Telegram login, admin login, refresh and logout."""

from __future__ import annotations

import logging
import secrets
from typing import Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import rate_limit, sessions, telegram_oidc
from app.config import settings
from app.constants import ADMIN_SUBJECT, LOGIN_STATE_COOKIE, REFRESH_COOKIE
from app.database import get_db
from app.models import User, UserRole
from app.redis_client import get_redis
from app.schemas import (
    AdminLoginRequest,
    AuthSuccessResponse,
    TelegramCallbackRequest,
    TelegramLoginStartResponse,
    TokenResponse,
    UserOut,
)
from app.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

LOGIN_STATE_KEY = "tg_login:{state}"
LOGIN_RATE_SCOPE = "telegram-login"
ADMIN_RATE_SCOPE = "admin-login"
RATE_WINDOW_SECONDS = 60


def _cookie_options() -> dict:
    return {"httponly": True, "secure": settings.cookie_secure, "samesite": "lax"}


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE, value=token, max_age=settings.refresh_token_expire_minutes * 60, **_cookie_options()
    )


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _role_value(user: User) -> Optional[str]:
    return user.role.value if user.role else None


async def _issue_tokens(response: Response, user: User) -> str:
    """Create a session, set the refresh cookie and return a new access token."""
    role = _role_value(user)
    _set_refresh_cookie(response, await sessions.create_session(str(user.id), role))
    return create_access_token(user.id, role)


def _refresh_telegram_picture(user: User, picture: Optional[str]) -> None:
    """Replace a stored Telegram picture with the current one: the old URL stops working once the user
    changes the photo in Telegram. A picture on another host is the user's own upload and is kept."""
    current = user.profile_picture_url
    if picture and (not current or urlsplit(current).netloc == urlsplit(picture).netloc):
        user.profile_picture_url = picture


async def _upsert_user(db: AsyncSession, profile: telegram_oidc.TelegramProfile) -> User:
    """Create the user on first login. Later logins keep the profile the user edited."""
    user = await db.get(User, profile.telegram_id)
    other = (await db.execute(select(User).where(User.phone == profile.phone))).scalar_one_or_none()
    if other is not None and other.id != profile.telegram_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This phone number belongs to another account.")

    if user is None:
        user = User(
            id=profile.telegram_id,
            full_name=profile.full_name,
            phone=profile.phone,
            telegram_username=profile.username,
            profile_picture_url=profile.picture,
            is_verified=True,
        )
        db.add(user)
    else:
        user.phone = profile.phone
        user.telegram_username = profile.username
        _refresh_telegram_picture(user, profile.picture)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/telegram/start", response_model=TelegramLoginStartResponse, summary="Begin Telegram login")
async def telegram_start(request: Request, response: Response) -> TelegramLoginStartResponse:
    """Return the Telegram authorization URL and bind the attempt to this browser with a cookie."""
    if not settings.telegram_configured:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram login is not configured.")
    await rate_limit.enforce_rate_limit(
        LOGIN_RATE_SCOPE, rate_limit.client_ip(request), settings.login_rate_limit_per_minute, RATE_WINDOW_SECONDS
    )

    state = secrets.token_urlsafe(32)
    verifier, challenge = telegram_oidc.new_pkce_pair()
    await get_redis().set(LOGIN_STATE_KEY.format(state=state), verifier, ex=settings.telegram_login_ttl_seconds)
    response.set_cookie(key=LOGIN_STATE_COOKIE, value=state, max_age=settings.telegram_login_ttl_seconds, **_cookie_options())
    return TelegramLoginStartResponse(authorization_url=telegram_oidc.build_authorization_url(state, challenge))


@router.post("/telegram/callback", response_model=AuthSuccessResponse, summary="Finish Telegram login")
async def telegram_callback(
    payload: TelegramCallbackRequest,
    request: Request,
    response: Response,
    login_state: Optional[str] = Cookie(None, alias=LOGIN_STATE_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> AuthSuccessResponse:
    """Exchange the Telegram code, verify the identity and sign the user in."""
    if not settings.telegram_configured:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram login is not configured.")
    await rate_limit.enforce_rate_limit(
        LOGIN_RATE_SCOPE, rate_limit.client_ip(request), settings.login_rate_limit_per_minute, RATE_WINDOW_SECONDS
    )

    # The state must come back from the same browser that started the login (prevents login CSRF).
    if not login_state or not secrets.compare_digest(login_state, payload.state):
        raise _bad_request("Login attempt does not match this browser. Please start again.")
    verifier = await get_redis().getdel(LOGIN_STATE_KEY.format(state=payload.state))
    if verifier is None:
        raise _bad_request("Login attempt expired. Please start again.")

    try:
        id_token = await telegram_oidc.exchange_code(payload.code, verifier)
        profile = await telegram_oidc.verify_id_token(id_token)
    except telegram_oidc.TelegramAuthError as exc:
        raise _bad_request(str(exc)) from exc

    user = await _upsert_user(db, profile)
    response.delete_cookie(LOGIN_STATE_COOKIE, **_cookie_options())
    access_token = await _issue_tokens(response, user)
    logger.info("Telegram login: user_id=%s", user.id)
    return AuthSuccessResponse(access_token=access_token, needs_role=user.role is None, user=UserOut.model_validate(user))


@router.post("/admin-login", response_model=AuthSuccessResponse, summary="Root admin login")
async def admin_login(payload: AdminLoginRequest, request: Request, response: Response) -> AuthSuccessResponse:
    """Authenticate the root admin from environment credentials. Repeated failures lock the login."""
    identity = f"{rate_limit.client_ip(request)}:{payload.username.lower()}"
    if await rate_limit.is_locked(ADMIN_RATE_SCOPE, identity, settings.admin_login_max_failures):
        raise HTTPException(status_code=rate_limit.TOO_MANY_REQUESTS, detail="Too many failed attempts. Try again later.")

    matches = secrets.compare_digest(payload.username, settings.admin_username)
    matches &= secrets.compare_digest(payload.password, settings.admin_password)
    if not matches:
        await rate_limit.record_failure(ADMIN_RATE_SCOPE, identity, settings.admin_login_lockout_seconds)
        logger.warning("Failed admin login for username=%s", payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await rate_limit.clear(ADMIN_RATE_SCOPE, identity)
    role = UserRole.admin.value
    _set_refresh_cookie(response, await sessions.create_session(ADMIN_SUBJECT, role))
    return AuthSuccessResponse(access_token=create_access_token(ADMIN_SUBJECT, role))


@router.post("/refresh", response_model=TokenResponse, summary="Rotate the refresh token")
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Issue a new access token and replace the refresh token. Each refresh token works once."""
    session = await sessions.consume_session(refresh_token) if refresh_token else None
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    role = session.role
    if session.subject != ADMIN_SUBJECT:
        user = await db.get(User, int(session.subject))
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        role = _role_value(user)

    _set_refresh_cookie(response, await sessions.create_session(session.subject, role))
    return TokenResponse(access_token=create_access_token(session.subject, role))


@router.post("/logout", summary="Revoke the refresh token")
async def logout(response: Response, refresh_token: Optional[str] = Cookie(None, alias=REFRESH_COOKIE)) -> dict:
    if refresh_token:
        await sessions.revoke_session(refresh_token)
    response.delete_cookie(REFRESH_COOKIE, **_cookie_options())
    return {"success": True, "message": "Logged out successfully"}
