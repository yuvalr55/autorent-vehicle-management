from datetime import datetime, timezone
from httpx import AsyncClient
from app.models.event_log import EventLog
from tests.conftest import _db_session_factory


async def _insert_event(event_type: str, data: dict) -> None:
    async with _db_session_factory() as session:
        session.add(EventLog(event_type=event_type, data=data, created_at=datetime.now(timezone.utc)))
        await session.commit()


async def test_events_empty_list(client: AsyncClient):
    response = await client.get("/events")
    assert response.status_code == 200
    assert response.json() == []


async def test_events_returns_inserted_entries(client: AsyncClient):
    await _insert_event("car.created", {"id": 1, "model": "Tesla"})
    await _insert_event("rental.started", {"rental_id": 1, "car_id": 1})
    response = await client.get("/events")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_events_filter_by_type(client: AsyncClient):
    await _insert_event("car.created", {"id": 1})
    await _insert_event("car.deleted", {"id": 1})
    await _insert_event("rental.started", {"rental_id": 1})
    response = await client.get("/events?event_type=car.created")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "car.created"


async def test_events_limit(client: AsyncClient):
    for i in range(5):
        await _insert_event("car.created", {"id": i})
    response = await client.get("/events?limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3


async def test_events_invalid_limit_returns_422(client: AsyncClient):
    assert (await client.get("/events?limit=0")).status_code == 422
    assert (await client.get("/events?limit=1001")).status_code == 422
