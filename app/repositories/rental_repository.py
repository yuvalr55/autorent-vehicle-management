from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rental import Rental


class RentalRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> List[Rental]:
        result = await self.db.execute(select(Rental).order_by(Rental.id))
        return list(result.scalars().all())

    async def get_by_id(self, rental_id: int) -> Optional[Rental]:
        result = await self.db.execute(select(Rental).where(Rental.id == rental_id))
        return result.scalar_one_or_none()

    async def has_active_for_car(self, car_id: int) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(Rental).where(
                Rental.car_id == car_id, Rental.is_active.is_(True)
            )
        )
        return result.scalar_one() > 0

    async def has_any_for_car(self, car_id: int) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(Rental).where(Rental.car_id == car_id)
        )
        return result.scalar_one() > 0

    async def count_active(self) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Rental).where(Rental.is_active.is_(True))
        )
        return result.scalar_one()
