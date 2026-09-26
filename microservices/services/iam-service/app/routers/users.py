"""IAM users router: profile, role selection and public profiles."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import MAX_PUBLIC_PROFILE_IDS
from app.database import get_db
from app.models import User, UserRole
from app.schemas import AuthSuccessResponse, PublicProfileOut, RoleSelectRequest, UserOut, UserUpdate
from app.security import create_access_token, get_current_user

router = APIRouter(tags=["Users"])

UNPROCESSABLE_STATUS = 422


def _is_synthetic_admin(user: User) -> bool:
    return user.id == 0 and user.role == UserRole.admin


@router.get("/users/me", response_model=UserOut, summary="Get current user profile")
@router.get("/auth/me", response_model=UserOut, include_in_schema=False)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("/users/me", response_model=UserOut, summary="Update current user profile")
async def update_current_user(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update the editable profile fields (name, university, picture)."""
    if _is_synthetic_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Synthetic admin profile cannot be updated.")

    data = payload.model_dump(exclude_unset=True)
    updates = {
        "full_name": data.get("full_name") or data.get("ism"),
        "university": data.get("university") or data.get("universitet"),
        "profile_picture_url": data.get("profile_picture_url") or data.get("rasm_url"),
    }
    for key, value in updates.items():
        if value is not None:
            setattr(current_user, key, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.put("/users/me/role", response_model=AuthSuccessResponse, summary="Choose a role (once)")
async def select_role(
    payload: RoleSelectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuthSuccessResponse:
    """Set the role after the first login. Returns a new access token that carries the role."""
    if _is_synthetic_admin(current_user) or current_user.role is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="The role has already been chosen.")

    current_user.role = UserRole(payload.role.value)
    await db.commit()
    await db.refresh(current_user)
    return AuthSuccessResponse(
        access_token=create_access_token(current_user.id, current_user.role.value),
        user=UserOut.model_validate(current_user),
    )


@router.get(
    "/users/public",
    response_model=list[PublicProfileOut],
    summary="Public profiles by ids (internal services only, not routed by the gateway)",
)
async def get_public_profiles(
    ids: str = Query(..., description="Comma-separated user ids"),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    """Return contact-safe profiles for the given user ids. Unknown ids are skipped."""
    try:
        user_ids = {int(raw) for raw in ids.split(",") if raw.strip()}
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE_STATUS, detail="ids must be integers.") from exc
    if len(user_ids) > MAX_PUBLIC_PROFILE_IDS:
        raise HTTPException(status_code=UNPROCESSABLE_STATUS, detail=f"At most {MAX_PUBLIC_PROFILE_IDS} ids are allowed.")
    if not user_ids:
        return []

    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return list(result.scalars().all())


@router.get("/users/{user_id}", response_model=UserOut, summary="Get user by id")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return a user profile. Non-admin users can only fetch themselves."""
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own profile.")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
