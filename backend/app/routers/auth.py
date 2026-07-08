import time
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas.auth import AuthSuccessResponse, LoginRequest, OtpVerifyRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut
from app.utils.security import create_token, hash_password, verify_otp_code, verify_password
from database.operations.insert import users as insert_users
from database.operations.select import users as select_users
from database.operations.update import users as update_users

router = APIRouter()


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_minutes * 60,
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> User:
    """Register a new user."""
    if await select_users.get_by_phone(db, payload.phone) is not None:
        raise HTTPException(status_code=400, detail="Phone number is already registered")

    if payload.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Cannot register with admin role")

    user = User(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        role=payload.role,
        university=payload.university,
        hashed_password=hash_password(payload.password) if payload.password else "",
        is_verified=False,
    )
    return await insert_users.create(db, user)


@router.post("/login", response_model=AuthSuccessResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccessResponse:
    """Login with phone and password."""
    try:
        user = await select_users.get_by_phone(db, payload.phone)

        if user is None or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid phone or password")

        if user.role == UserRole.admin:
            raise HTTPException(status_code=403, detail="Use the admin portal to sign in as admin")

        access_token = create_token(str(user.id), expires_minutes=settings.access_token_expire_minutes)
        refresh_token = create_token(str(user.id), expires_minutes=settings.refresh_token_expire_minutes)
        set_refresh_cookie(response, refresh_token)
        return AuthSuccessResponse(
            access_token=access_token,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Login failed: " + str(e))


@router.post("/admin-login", response_model=AuthSuccessResponse)
async def admin_login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccessResponse:
    """Admin panel login (hidden endpoint)."""
    user = await select_users.get_by_phone(db, payload.phone)

    if user is None or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid phone or password")

    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only admins can access the admin panel")

    access_token = create_token(str(user.id), expires_minutes=settings.access_token_expire_minutes)
    refresh_token = create_token(str(user.id), expires_minutes=settings.refresh_token_expire_minutes)
    set_refresh_cookie(response, refresh_token)
    return AuthSuccessResponse(
        access_token=access_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    payload: Optional[RefreshRequest] = Body(default=None),
) -> TokenResponse:
    """Refresh access token."""
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


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(payload: OtpVerifyRequest, response: Response, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Verify OTP for phone-based registration."""
    if not verify_otp_code(payload.phone, payload.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    user = await select_users.get_by_phone(db, payload.phone)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await update_users.verify_user(db, user.id)

    access_token = create_token(str(user.id), expires_minutes=settings.access_token_expire_minutes)
    refresh_token = create_token(str(user.id), expires_minutes=settings.refresh_token_expire_minutes)
    set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(response: Response) -> dict[str, object]:
    """Logout user."""
    response.delete_cookie("refresh_token")
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated user."""
    return current_user


@router.get("/bot/check/{phone}")
async def check_user_by_phone(phone: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Check if user exists by phone (for bot registration)."""
    user = await select_users.get_by_phone(db, phone)

    if user:
        return {
            "success": True,
            "data": {
                "exists": True,
                "id": str(user.id),
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
                "is_verified": user.is_verified,
            }
        }

    return {
        "success": True,
        "data": {
            "exists": False
        }
    }
