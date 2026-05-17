from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.events.publisher import EventPublisher, get_publisher
from app.services.car_service import CarService
from app.schemas.car import CarCreate, CarUpdate, CarResponse
from app.enums import CarStatus

router = APIRouter(prefix="/cars", tags=["Cars"])


@router.post(
    "",
    response_model=CarResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new car to the fleet",
)
async def create_car(data: CarCreate, db: AsyncSession = Depends(get_db), publisher: EventPublisher = Depends(get_publisher)) -> CarResponse:
    return await CarService(db, publisher).add_car(data)


@router.get(
    "",
    response_model=List[CarResponse],
    summary="List all cars, optionally filtered by status",
)
async def list_cars(
    status: Optional[CarStatus] = Query(None, description="Filter cars by status"),
    db: AsyncSession = Depends(get_db),
) -> List[CarResponse]:
    return await CarService(db).list_cars(status=status)


@router.get(
    "/{car_id}",
    response_model=CarResponse,
    summary="Get a single car by ID",
)
async def get_car(car_id: int, db: AsyncSession = Depends(get_db)) -> CarResponse:
    return await CarService(db).get_car(car_id)


@router.patch(
    "/{car_id}",
    response_model=CarResponse,
    summary="Update car details (model, year, or status)",
)
async def update_car(car_id: int, data: CarUpdate, db: AsyncSession = Depends(get_db), publisher: EventPublisher = Depends(get_publisher)) -> CarResponse:
    return await CarService(db, publisher).update_car(car_id, data)


@router.delete(
    "/{car_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a car from the fleet",
)
async def delete_car(car_id: int, db: AsyncSession = Depends(get_db), publisher: EventPublisher = Depends(get_publisher)) -> None:
    await CarService(db, publisher).delete_car(car_id)
