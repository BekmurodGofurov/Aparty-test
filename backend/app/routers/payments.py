import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.payment import Payment
from app.models.user import User, UserRole
from app.schemas.payment import PaymentCreate, PaymentOut, PaymentStatusUpdate, PaymentUpdate
from database.operations.delete import payments as delete_payments
from database.operations.insert import payments as insert_payments
from database.operations.select import payments as select_payments
from database.operations.update import payments as update_payments

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
    return await insert_payments.create(db, payment)


@router.get("/", response_model=list[PaymentOut])
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Payment]:
    """List payments for current user"""
    return await select_payments.list_by_payer(db, current_user.id, skip=skip, limit=limit)


@router.get("/user/{user_id}", response_model=list[PaymentOut])
async def get_user_payments(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Payment]:
    """Get payments for a user"""
    if user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Bu tolovlarga kirish ruxsati yo'q")
    return await select_payments.get_by_payer_id(db, user_id)


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Payment:
    """Get payment details"""
    payment = await select_payments.get_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")

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
    payment = await select_payments.get_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")

    updated = await update_payments.update_status(db, payment_id, payload.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")
    return updated


@router.patch("/{payment_id}", response_model=PaymentOut)
async def edit_payment(
    payment_id: uuid.UUID,
    payload: PaymentUpdate,
    current_user: User = Depends(require_roles("admin", "makler")),
    db: AsyncSession = Depends(get_db),
) -> Payment:
    """Edit payment details (admin and broker only)"""
    payment = await select_payments.get_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")

    updated = await update_payments.update_fields(
        db,
        payment_id,
        amount=payload.amount,
        billing_month=payload.billing_month,
        status=payload.status,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")
    return updated


@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(require_roles("admin", "makler")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete payment (admin and broker only)"""
    payment = await select_payments.get_by_id(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Tolov topilmadi")

    await delete_payments.delete_by_id(db, payment_id)
    return {"message": "Tolov muvaffaqiyatli o'chirildi", "payment_id": str(payment_id)}
