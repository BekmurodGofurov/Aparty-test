"""RabbitMQ consumer of the Notification Service."""

from __future__ import annotations

import asyncio
import logging

from app.constants import CONSUMED_EVENTS, EVENT_QUEUE
from app.handlers import handle_event
from app.rabbitmq import start_consumer

logger = logging.getLogger(__name__)

CONSUMER_RETRY_SECONDS = 5


async def run_consumer() -> None:
    """Keep trying to start the consumer until the broker is reachable."""
    while True:
        try:
            await start_consumer(EVENT_QUEUE, CONSUMED_EVENTS, handle_event)
            return
        except Exception as exc:
            logger.warning("Event consumer not started (%s). Retrying in %ss.", exc, CONSUMER_RETRY_SECONDS)
            await asyncio.sleep(CONSUMER_RETRY_SECONDS)
