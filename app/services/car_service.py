from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import event_types
from app.events.publisher import EventPublisher
from app.logging_config import get_logger
from app.models.car import Car
from app.repositories.car_repository import CarRepository
from app.repositories.rental_repository import RentalRepository
from app.schemas.car import CarCreate, CarUpdate
from app.enums import CarStatus

logger = get_logger(__name__)


class CarService:
    def __init__(self, db: AsyncSession, publisher: Optional[EventPublisher] = None) -> None:
        self.repo = CarRepository(db)
        self.rental_repo = RentalRepository(db)
        self.publisher = publisher

    async def add_car(self, data: CarCreate) -> Car:
        car = await self.repo.create(model=data.model, year=data.year, status=data.status)
        logger.info("Car added: id=%d model=%s year=%d", car.id, car.model, car.year)
        if self.publisher:
            await self.publisher.publish(event_types.CAR_CREATED, {
                "id": car.id, "model": car.model, "year": car.year, "status": car.status.value,
            })
        return car

    async def get_car(self, car_id: int) -> Car:
        return await self._get_or_404(car_id)

    async def list_cars(self, status: Optional[CarStatus] = None) -> List[Car]:
        return await self.repo.get_all(status=status)

    async def update_car(self, car_id: int, data: CarUpdate) -> Car:
        car = await self._get_or_404(car_id)
        updates = data.model_dump(exclude_none=True)
        if not updates:
            return car
        car = await self.repo.update(car, **updates)
        logger.info("Car updated: id=%d fields=%s", car.id, list(updates.keys()))
        if self.publisher:
            await self.publisher.publish(event_types.CAR_UPDATED, {
                "id": car.id, "fields": updates,
            })
        return car

    async def delete_car(self, car_id: int) -> None:
        car = await self._get_or_404(car_id)
        if await self.rental_repo.has_any_for_car(car_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Car {car_id} cannot be deleted because it has rental records",
            )
        await self.repo.delete(car)
        logger.info("Car deleted: id=%d", car_id)
        if self.publisher:
            await self.publisher.publish(event_types.CAR_DELETED, {"id": car_id})

    async def _get_or_404(self, car_id: int) -> Car:
        car = await self.repo.get_by_id(car_id)
        if not car:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Car {car_id} not found")
        return car
