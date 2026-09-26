"""Catalog Service RabbitMQ Publisher module.

Handles event publishing to topic exchange `aparty.events`.
"""

from __future__ import annotations

import json
import logging
from urllib.parse import urlsplit
from typing import Any, Dict

import aio_pika
from app.config import settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "aparty.events"

_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None
_exchange: aio_pika.abc.AbstractExchange | None = None


async def init_rabbitmq() -> None:
    """Initialize robust RabbitMQ connection and exchange."""
    global _connection, _channel, _exchange
    try:
        logger.info("Connecting to RabbitMQ at %s", urlsplit(settings.rabbitmq_url).hostname)
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        _channel = await _connection.channel()
        _exchange = await _channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )
        logger.info("RabbitMQ exchange '%s' ready.", EXCHANGE_NAME)
    except Exception as e:
        logger.warning("RabbitMQ connection failed on startup: %s. Events will be retried.", e)


async def close_rabbitmq() -> None:
    """Close RabbitMQ connection gracefully."""
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
        logger.info("RabbitMQ connection closed.")


async def publish_event(routing_key: str, payload: Dict[str, Any]) -> None:
    """Publish event payload to RabbitMQ exchange under `routing_key`."""
    global _exchange, _connection
    if not _exchange or (_connection and _connection.is_closed):
        try:
            await init_rabbitmq()
        except Exception as e:
            logger.error("Failed to re-initialize RabbitMQ: %s", e)
            return

    if not _exchange:
        logger.error("RabbitMQ exchange unavailable, cannot publish event '%s'", routing_key)
        return

    try:
        body = json.dumps(payload, default=str).encode("utf-8")
        message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await _exchange.publish(message, routing_key=routing_key)
        logger.info("Published RabbitMQ event '%s': %s", routing_key, payload)
    except Exception as e:
        logger.error("Error publishing RabbitMQ event '%s': %s", routing_key, e)


async def start_consumer(queue_name: str, routing_keys: list[str], handler) -> None:
    """Consume events bound to `routing_keys`. `handler` receives the decoded JSON payload.

    A failing handler requeues the message once; a second failure drops it.
    """
    if not _channel or not _exchange:
        await init_rabbitmq()
    if not _channel or not _exchange:
        raise RuntimeError("RabbitMQ is unavailable")

    queue = await _channel.declare_queue(queue_name, durable=True)
    for routing_key in routing_keys:
        await queue.bind(_exchange, routing_key=routing_key)

    async def on_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process(requeue=True, reject_on_redelivered=True):
            await handler(json.loads(message.body))

    await queue.consume(on_message)
    logger.info("Consuming '%s' from queue '%s'.", ", ".join(routing_keys), queue_name)
