import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from app.database import get_engine, Base
import app.models  # noqa: F401 — registers Car and Rental with Base.metadata
from app.api import cars, rentals
from app.api.metrics_router import router as metrics_router
from app.api.events import router as events_router
from app.logging_config import setup_logging
from app.metrics import request_duration_histogram

setup_logging()


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="AutoRent — Vehicle Management System",
    description=(
        "Internal fleet management API for AutoRent car rental platform.\n\n"
        "Manage vehicles, register rentals, and monitor fleet metrics."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.middleware("http")
async def track_request_duration(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    request_duration_histogram.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)
    return response


app.include_router(cars.router)
app.include_router(rentals.router)
app.include_router(metrics_router)
app.include_router(events_router)
