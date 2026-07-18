from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from database.operations.select import users as select_users

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _get_memory_admin_user() -> User:
    """Return an in-memory dummy User object representing the Root Admin."""
    return User(
        id=0,  # Dummy ID (not stored in DB)
        full_name="System Admin",
        phone="+998000000000",
        role=UserRole.admin,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub = payload.get("sub")
        role = payload.get("role")
        if sub is None:
            raise credentials_exception

        # Bypass DB check for Root Admin token
        if str(sub).lower() == "admin" and str(role).lower() == "admin":
            return _get_memory_admin_user()

        # users.id is a BigInteger (Telegram ID) — parse as int
        user_id = int(sub)
    except (JWTError, ValueError) as exc:
        raise credentials_exception from exc

    user = await select_users.get_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_optional_current_user(
    token: str | None = Depends(optional_oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub = payload.get("sub")
        role = payload.get("role")
        if sub is None:
            return None

        if str(sub).lower() == "admin" and str(role).lower() == "admin":
            return _get_memory_admin_user()

        user_id = int(sub)
    except (JWTError, ValueError):
        return None

    return await select_users.get_by_id(db, user_id)


def require_role(*role_names: str):
    """Check if user has one of the required roles."""

    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role is None or current_user.role.value not in role_names:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return checker


def require_roles(*role_names: str):
    """Alias for require_role for backward compatibility."""
    return require_role(*role_names)


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency specifically verifying root/admin role."""
    if current_user.role is None or current_user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")
    return current_user
