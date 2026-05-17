from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.repositories.event_log_repository import EventLogRepository
from app.schemas.event_log import EventLogResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.get(
    "",
    response_model=List[EventLogResponse],
    summary="List audit log events, optionally filtered by type",
)
async def list_events(
    event_type: Optional[str] = Query(None, description="Filter by event type (e.g. car.created)"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of events to return"),
    db: AsyncSession = Depends(get_db),
) -> List[EventLogResponse]:
    return await EventLogRepository(db).list(event_type=event_type, limit=limit)
