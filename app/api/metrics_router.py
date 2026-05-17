from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.database import get_db
from app.repositories.car_repository import CarRepository
from app.repositories.rental_repository import RentalRepository
from app.enums import CarStatus
from app import metrics

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    summary="Prometheus metrics endpoint",
    description="Returns current system metrics in Prometheus exposition format.",
    response_class=Response,
)
async def get_metrics(db: AsyncSession = Depends(get_db)) -> Response:
    car_repo = CarRepository(db)
    rental_repo = RentalRepository(db)

    metrics.update_car_metrics(
        active=await car_repo.count_by_status(CarStatus.in_use),
        available=await car_repo.count_by_status(CarStatus.available),
        maintenance=await car_repo.count_by_status(CarStatus.maintenance),
    )
    metrics.update_rental_metrics(ongoing=await rental_repo.count_active())

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
