from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from database.operations.delete import users as delete_users
from database.operations.select import users as select_users
from database.operations.update import users as update_users

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    """Get current user profile"""
    return current_user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    """Get user by ID (Telegram ID)"""
    user = await select_users.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return user


@router.put("/me", response_model=UserOut)
async def update_current_user(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Update current user profile"""
    update_data = payload.model_dump(exclude_unset=True)

    update_data.pop("role", None)
    update_data.pop("is_verified", None)

    if not update_data:
        return current_user

    updated = await update_users.update_fields(db, current_user.id, **update_data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return updated


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete current user account"""
    await delete_users.delete(db, current_user)
    return None
