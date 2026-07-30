"""RabbitMQ connection manager.

A single connection is created once at startup via ``create_rabbitmq_connection()`` and
stored on ``app.state.rabbitmq``. All consumers retrieve it from there.

Usage (in lifespan):
    rabbitmq = await create_rabbitmq_connection(settings.rabbitmq_url)
    app.state.rabbitmq = rabbitmq
"""

from __future__ import annotations

import logging
import aio_pika

logger = logging.getLogger(__name__)


async def create_rabbitmq_connection(url: str) -> aio_pika.RobustConnection:
    """Create and return a connected async RabbitMQ robust connection.

    This uses aio_pika.connect_robust which automatically handles reconnects
    if the connection is lost (robustness).

    Args:
        url: RabbitMQ connection URL.

    Returns:
        A live ``aio_pika.RobustConnection`` instance.
    """
    logger.debug("Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(url)
    logger.debug("Connected to RabbitMQ successfully.")
    return connection
