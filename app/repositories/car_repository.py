from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.car import Car
from app.enums import CarStatus


class CarRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, model: str, year: int, status: CarStatus = CarStatus.available) -> Car:
        car = Car(model=model, year=year, status=status)
        self.db.add(car)
        await self.db.commit()
        await self.db.refresh(car)
        return car

    async def get_all(self, status: Optional[CarStatus] = None) -> List[Car]:
        stmt = select(Car)
        if status is not None:
            stmt = stmt.where(Car.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, car_id: int) -> Optional[Car]:
        result = await self.db.execute(select(Car).where(Car.id == car_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, car_id: int) -> Optional[Car]:
        result = await self.db.execute(
            select(Car).where(Car.id == car_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def update(self, car: Car, **fields) -> Car:
        for key, value in fields.items():
            setattr(car, key, value)
        await self.db.commit()
        await self.db.refresh(car)
        return car

    async def delete(self, car: Car) -> None:
        await self.db.delete(car)
        await self.db.commit()

    async def count_by_status(self, status: CarStatus) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Car).where(Car.status == status)
        )
        return result.scalar_one()
