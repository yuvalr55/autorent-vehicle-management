from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.test", override=True)

import os
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.database import Base, get_db
from app.events.publisher import EventPublisher, get_publisher
from app.main import app

_test_url = os.environ["DATABASE_URL"]
_test_engine = create_async_engine(_test_url, poolclass=NullPool)
_db_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


class _NoOpPublisher(EventPublisher):
    def __init__(self) -> None:
        pass

    async def publish(self, event_type: str, data: dict) -> None:
        pass


@asynccontextmanager
async def _noop_lifespan(_):
    yield


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def client():
    async def _override_db():
        async with _db_session_factory() as session:
            yield session

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_publisher] = lambda: _NoOpPublisher()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan
