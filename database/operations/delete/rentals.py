import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rental import Rental

from database.operations.select import rentals as select_rentals


async def delete_rental(db: AsyncSession, rental_id: uuid.UUID) -> bool:
    rental = await select_rentals.get_rental_by_id(db, rental_id)
    if rental is None:
        return False
    await db.delete(rental)
    await db.commit()
    return True
