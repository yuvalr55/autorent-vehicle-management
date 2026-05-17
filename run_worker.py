from dotenv import load_dotenv
import asyncio
import app.models  # noqa: F401 — registers all models with Base.metadata
from app.database import get_engine, Base
from app.events.consumer import run

load_dotenv()


async def main() -> None:
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await run()


if __name__ == "__main__":
    asyncio.run(main())
