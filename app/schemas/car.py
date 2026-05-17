from pydantic import BaseModel, Field
from typing import Optional
from app.enums import CarStatus


class CarCreate(BaseModel):
    model: str = Field(..., min_length=1, max_length=100, examples=["Tesla Model 3"])
    year: int = Field(..., ge=1900, le=2100, examples=[2023])
    status: CarStatus = CarStatus.available


class CarUpdate(BaseModel):
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    status: Optional[CarStatus] = None


class CarResponse(BaseModel):
    id: int
    model: str
    year: int
    status: CarStatus

    model_config = {"from_attributes": True}
