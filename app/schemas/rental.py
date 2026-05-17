from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class RentalCreate(BaseModel):
    car_id: int = Field(..., gt=0)
    customer_name: str = Field(..., min_length=1, max_length=100, examples=["John Doe"])
    start_date: date = Field(..., examples=["2024-01-15"])


class RentalResponse(BaseModel):
    id: int
    car_id: int
    customer_name: str
    start_date: date
    end_date: Optional[date] = None
    is_active: bool

    model_config = {"from_attributes": True}
