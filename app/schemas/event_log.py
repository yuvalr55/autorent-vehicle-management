from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel


class EventLogResponse(BaseModel):
    id: int
    event_type: str
    data: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}
