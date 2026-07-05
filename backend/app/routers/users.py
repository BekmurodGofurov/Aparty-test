import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate
from app.utils.security import hash_password

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    """Get current user profile"""
    return current_user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> User:
    """Get user by UUID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
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
    
    # Handle password update if provided
    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))
    
    # Ensure we don't update certain fields
    update_data.pop("role", None)  # Role cannot be changed
    update_data.pop("is_verified", None)  # Verification status is admin-only
    
    if not update_data:
        return current_user
        
    stmt = update(User).where(User.id == current_user.id).values(**update_data)
    await db.execute(stmt)
    await db.commit()
    
    result = await db.execute(select(User).where(User.id == current_user.id))
    return result.scalar_one()


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete current user account"""
    await db.delete(current_user)
    await db.commit()
    return None
