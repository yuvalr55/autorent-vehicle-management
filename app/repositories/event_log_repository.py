from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event_log import EventLog


class EventLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self, event_type: Optional[str] = None, limit: int = 100) -> List[EventLog]:
        q = select(EventLog)
        if event_type:
            q = q.where(EventLog.event_type == event_type)
        q = q.order_by(EventLog.created_at.desc()).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()
