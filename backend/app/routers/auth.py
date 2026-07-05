import time
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas.auth import AuthSuccessResponse, LoginRequest, OtpVerifyRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut
from app.utils.security import create_token, hash_password, verify_password

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
    """Register a new user"""
    existing_phone = await db.execute(select(User).where(User.phone == payload.phone))
    if existing_phone.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="Telefon raqam allaqachon ro'yxatdan o'tgan")

    # Prevent direct admin registration
    if payload.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Admin roli orqali ro'yxatdan o'ta olmaysiz")

    user = User(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        role=payload.role,
        university=payload.university,
        hashed_password=hash_password(payload.password) if payload.password else "",
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=AuthSuccessResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccessResponse:
    """Login with phone and password"""
    try:
        result = await db.execute(select(User).where(User.phone == payload.phone))
        user = result.scalar_one_or_none()

        if user is None or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Telefon yoki parol xato")

        # Prevent admin login through regular endpoint
        if user.role == UserRole.admin:
            raise HTTPException(status_code=403, detail="Admin panelga kirish uchun maxsus portal'dan foydalaning")

        access_token = create_token(str(user.id), expires_minutes=settings.access_token_expire_minutes)
        refresh_token = create_token(str(user.id), expires_minutes=settings.refresh_token_expire_minutes)
        set_refresh_cookie(response, refresh_token)
        return AuthSuccessResponse(
            access_token=access_token,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Login jarayonida xatolik: " + str(e))


@router.post("/admin-login", response_model=AuthSuccessResponse)
async def admin_login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthSuccessResponse:
    """Admin panel login (hidden endpoint)"""
    result = await db.execute(select(User).where(User.phone == payload.phone))
    user = result.scalar_one_or_none()

    if user is None or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Telefon yoki parol xato")

    # Only allow admin role
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin panelga faqat admin kirishga ruxsat")

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
    """Refresh access token"""
    token = request.cookies.get("refresh_token") or (payload.refresh_token if payload else None)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token yo'q")

    try:
        data = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = data.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Refresh token yaroqsiz")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Refresh token yaroqsiz") from exc

    return TokenResponse(
        message="Access token yangilandi",
        access_token=create_token(str(user_id), expires_minutes=settings.access_token_expire_minutes),
    )


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(payload: OtpVerifyRequest, response: Response, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Verify OTP for phone-based registration"""
    result = await db.execute(select(User).where(User.phone == payload.phone))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User topilmadi")
    
    access_token = create_token(str(user.id), expires_minutes=settings.access_token_expire_minutes)
    refresh_token = create_token(str(user.id), expires_minutes=settings.refresh_token_expire_minutes)
    set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(response: Response) -> dict[str, object]:
    """Logout user"""
    response.delete_cookie("refresh_token")
    return {"success": True, "message": "Muvaffaqiyatli logout qilindi"}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated user"""
    return current_user


@router.get("/bot/check/{phone}")
async def check_user_by_phone(phone: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Check if user exists by phone (for bot registration)"""
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    
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
