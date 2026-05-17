import asyncio
import json
import os

import aio_pika

from app.database import AsyncSessionLocal
from app.models.event_log import EventLog
from app.logging_config import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

_ROUTING_KEYS = ["car.*", "rental.*"]


async def _persist_event(event_type: str, data: dict) -> None:
    async with AsyncSessionLocal() as session:
        session.add(EventLog(event_type=event_type, data=data))
        await session.commit()


async def _handle_event(event_type: str, data: dict) -> None:
    await _persist_event(event_type, data)
    logger.info("Event logged: %s data=%s", event_type, data)


async def run() -> None:
    rabbitmq_url = os.environ["RABBITMQ_URL"]
    exchange_name = os.environ["RABBITMQ_EXCHANGE"]
    queue_name = os.environ["RABBITMQ_QUEUE"]
    concurrency = int(os.environ["WORKER_CONCURRENCY"])

    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=concurrency)
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue(queue_name, durable=True)

        for routing_key in _ROUTING_KEYS:
            await queue.bind(exchange, routing_key=routing_key)

        logger.info("Event consumer started — exchange: %s  concurrency: %d", exchange_name, concurrency)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    payload = json.loads(message.body)
                    event_type = payload["event"]
                except (json.JSONDecodeError, KeyError) as exc:
                    logger.error("Malformed message, discarding: %s — body=%r", exc, message.body[:200])
                    await message.reject(requeue=False)
                    continue

                async with message.process(requeue=True):
                    try:
                        await _handle_event(event_type, payload.get("data", {}))
                    except Exception as exc:
                        logger.error("Failed to persist event %s, requeueing: %s", event_type, exc)
                        raise


if __name__ == "__main__":
    asyncio.run(run())
