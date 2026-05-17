from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.events.publisher import EventPublisher, get_publisher
from app.services.rental_service import RentalService
from app.schemas.rental import RentalCreate, RentalResponse

router = APIRouter(prefix="/rentals", tags=["Rentals"])


@router.get(
    "",
    response_model=List[RentalResponse],
    summary="List all rentals",
)
async def list_rentals(db: AsyncSession = Depends(get_db)) -> List[RentalResponse]:
    return await RentalService(db).list_rentals()


@router.get(
    "/{rental_id}",
    response_model=RentalResponse,
    summary="Get a single rental by ID",
)
async def get_rental(rental_id: int, db: AsyncSession = Depends(get_db)) -> RentalResponse:
    return await RentalService(db).get_rental(rental_id)


@router.post(
    "",
    response_model=RentalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new rental for an available car",
)
async def start_rental(data: RentalCreate, db: AsyncSession = Depends(get_db), publisher: EventPublisher = Depends(get_publisher)) -> RentalResponse:
    return await RentalService(db, publisher).start_rental(data)


@router.post(
    "/{rental_id}/end",
    response_model=RentalResponse,
    summary="End an active rental and return the car to available status",
)
async def end_rental(rental_id: int, db: AsyncSession = Depends(get_db), publisher: EventPublisher = Depends(get_publisher)) -> RentalResponse:
    return await RentalService(db, publisher).end_rental(rental_id)
