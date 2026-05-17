import json
import os
from datetime import datetime, timezone
from typing import Optional

import aio_pika

from app.logging_config import get_logger

logger = get_logger(__name__)


class EventPublisher:
    def __init__(self) -> None:
        self._rabbitmq_url = os.environ["RABBITMQ_URL"]
        self._exchange_name = os.environ["RABBITMQ_EXCHANGE"]
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._exchange: Optional[aio_pika.Exchange] = None

    async def _get_exchange(self) -> aio_pika.Exchange:
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self._rabbitmq_url, timeout=5)
            channel = await self._connection.channel()
            self._exchange = await channel.declare_exchange(
                self._exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
            )
        return self._exchange  # type: ignore[return-value]

    async def publish(self, event_type: str, data: dict) -> None:
        payload = json.dumps({
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }).encode()
        try:
            exchange = await self._get_exchange()
            await exchange.publish(
                aio_pika.Message(payload, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=event_type,
            )
            logger.debug("Event published: %s", event_type)
        except Exception as exc:
            self._connection = None
            self._exchange = None
            logger.warning("Failed to publish event %s: %s", event_type, exc)


_publisher: Optional[EventPublisher] = None


def get_publisher() -> EventPublisher:
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher
