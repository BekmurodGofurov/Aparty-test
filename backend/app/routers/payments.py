import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role, require_roles
from app.models.payment import Payment
from app.models.user import User, UserRole
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentStatusUpdate, PaymentUpdate

router = APIRouter()


@router.post("/", response_model=PaymentOut)
async def create_payment(
    payload: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Payment:
    """Create a new payment"""
    if payload.payer_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Boshqa foydalanuvchi nomidan to'lov yaratib bo'lmaydi")
    payment = Payment(**payload.model_dump())
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("/", response_model=list[PaymentOut])
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Payment]:
    """List payments for current user"""
    result = await db.execute(
        select(Payment)
        .where(Payment.payer_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/user/{user_id}", response_model=list[PaymentOut])
async def get_user_payments(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Payment]:
    """Get payments for a user"""
    if user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Bu tolovlarga kirish ruxsati yo'q")
    result = await db.execute(select(Payment).where(Payment.payer_id == user_id))
    return result.scalars().all()


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Payment:
    """Get payment details"""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")
    
    # Check authorization
    if payment.payer_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Bu tolovga kirish ruxsati yo'q")
    
    return payment


@router.patch("/{payment_id}/status", response_model=PaymentOut)
async def update_payment_status(
    payment_id: uuid.UUID,
    payload: PaymentStatusUpdate,
    current_user: User = Depends(require_roles("admin", "makler")),
    db: AsyncSession = Depends(get_db),
) -> Payment:
    """Update payment status (admin and broker only)"""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")
    
    stmt = update(Payment).where(Payment.id == payment_id).values(status=payload.status)
    await db.execute(stmt)
    await db.commit()
    
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one()


@router.patch("/{payment_id}", response_model=PaymentOut)
async def edit_payment(
    payment_id: uuid.UUID,
    payload: PaymentUpdate,
    current_user: User = Depends(require_roles("admin", "makler")),
    db: AsyncSession = Depends(get_db),
) -> Payment:
    """Edit payment details (admin and broker only)"""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")
    
    stmt = (
        update(Payment)
        .where(Payment.id == payment_id)
        .values(
            amount=payload.amount,
            billing_month=payload.billing_month,
            status=payload.status
        )
    )
    await db.execute(stmt)
    await db.commit()
    
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    return result.scalar_one()


@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(require_roles("admin", "makler")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete payment (admin and broker only)"""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")
    
    stmt = delete(Payment).where(Payment.id == payment_id)
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Tolov muvaffaqiyatli o'chirildi", "payment_id": str(payment_id)}
