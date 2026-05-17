from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.events import event_types
from app.events.publisher import EventPublisher
from app.logging_config import get_logger
from app.models.rental import Rental
from app.repositories.car_repository import CarRepository
from app.repositories.rental_repository import RentalRepository
from app.schemas.rental import RentalCreate
from app.enums import CarStatus

logger = get_logger(__name__)


class RentalService:
    def __init__(self, db: AsyncSession, publisher: Optional[EventPublisher] = None) -> None:
        self.db = db
        self.car_repo = CarRepository(db)
        self.rental_repo = RentalRepository(db)
        self.publisher = publisher

    async def list_rentals(self) -> List[Rental]:
        return await self.rental_repo.get_all()

    async def get_rental(self, rental_id: int) -> Rental:
        return await self._get_rental_or_404(rental_id)

    async def start_rental(self, data: RentalCreate) -> Rental:
        # SELECT FOR UPDATE acquires a row-level lock, preventing concurrent
        # rentals of the same car between the availability check and the commit.
        car = await self.car_repo.get_by_id_for_update(data.car_id)
        if not car:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Car {data.car_id} not found")

        if car.status != CarStatus.available:
            logger.warning(
                "Rental rejected: car_id=%d status=%s customer=%s",
                car.id, car.status.value, data.customer_name,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Car {data.car_id} is not available (current status: {car.status.value})",
            )

        car.status = CarStatus.in_use
        rental = Rental(
            car_id=data.car_id,
            customer_name=data.customer_name,
            start_date=data.start_date,
        )
        self.db.add(rental)
        await self.db.commit()
        await self.db.refresh(rental)
        logger.info(
            "Rental started: rental_id=%d car_id=%d customer=%s",
            rental.id, car.id, data.customer_name,
        )
        if self.publisher:
            await self.publisher.publish(event_types.RENTAL_STARTED, {
                "rental_id": rental.id, "car_id": car.id, "customer_name": data.customer_name,
            })
        return rental

    async def end_rental(self, rental_id: int) -> Rental:
        rental = await self._get_rental_or_404(rental_id)

        if not rental.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Rental {rental_id} is already closed",
            )

        car = await self.car_repo.get_by_id(rental.car_id)
        if not car:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Car {rental.car_id} associated with rental {rental_id} not found",
            )

        rental.is_active = False
        rental.end_date = date.today()
        car.status = CarStatus.available
        await self.db.commit()
        await self.db.refresh(rental)
        logger.info("Rental ended: rental_id=%d car_id=%d", rental_id, rental.car_id)
        if self.publisher:
            await self.publisher.publish(event_types.RENTAL_ENDED, {
                "rental_id": rental_id, "car_id": rental.car_id,
            })
        return rental

    async def _get_rental_or_404(self, rental_id: int) -> Rental:
        rental = await self.rental_repo.get_by_id(rental_id)
        if not rental:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rental {rental_id} not found")
        return rental
