import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator

Base = declarative_base()

_engine = None
_session_factory = None


def get_engine():
    global _engine, _session_factory
    if _engine is None:
        url = os.environ["DATABASE_URL"]
        _engine = create_async_engine(url)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def AsyncSessionLocal():
    get_engine()
    return _session_factory()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    get_engine()
    async with _session_factory() as session:
        yield session
