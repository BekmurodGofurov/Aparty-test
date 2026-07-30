"""RabbitMQ Domain Event Bus.

This replaces the previous in-memory event bus to prepare for a microservices
architecture, allowing services to decouple and scale independently.

Design:
  - Uses RabbitMQ via aio_pika.
  - Subscribers are async coroutines registered at startup via ``subscribe()``.
  - ``publish()`` routes messages to a Topic Exchange ("aparty.events").
  - A background consumer binds a queue ("aparty.monolith.queue") and 
    listens for all subscribed routing keys.
  - aio-pika's robust connections automatically handle network disconnects 
    and reconnects (robustness).
  - Messages are automatically acknowledged (ACK) using message.process() 
    after successful local handler execution.

Microservice migration path:
    When the project graduates to microservices, the services can just listen 
    to their own queues bound to the "aparty.events" exchange.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

import aio_pika

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Registry: event_name → list[async handler]
_handlers: dict[str, list[Callable[..., Awaitable[Any]]]] = defaultdict(list)

# Global RabbitMQ publisher components
_rabbitmq_connection: aio_pika.RobustConnection | None = None
_publisher_channel: aio_pika.abc.AbstractChannel | None = None
_exchange: aio_pika.abc.AbstractExchange | None = None

EXCHANGE_NAME = "aparty.events"
QUEUE_NAME = "aparty.monolith.queue"


def subscribe(event: str, handler: Callable[..., Awaitable[Any]]) -> None:
    """Register *handler* to be called whenever *event* is published.

    Args:
        event: Dot-namespaced event string, e.g. ``"booking.confirmed"``.
        handler: An async callable accepting a single ``payload: BaseModel`` arg.
    """
    _handlers[event].append(handler)
    logger.debug("Subscribed %s to event '%s'.", handler.__qualname__, event)


async def setup_publisher(connection: aio_pika.RobustConnection) -> None:
    """Setup the publisher channel and exchange."""
    global _rabbitmq_connection, _publisher_channel, _exchange
    _rabbitmq_connection = connection
    _publisher_channel = await connection.channel()
    # aio_pika robust channels will auto-restore on reconnect
    _exchange = await _publisher_channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    logger.info("RabbitMQ publisher setup complete on exchange '%s'.", EXCHANGE_NAME)


async def publish(event: str, payload: BaseModel) -> None:
    """Publish *payload* to the RabbitMQ topic exchange using *event* as routing key.

    Args:
        event: The event name to publish (used as routing key).
        payload: Pydantic model to serialize as JSON.
    """
    if not _exchange:
        logger.error("Publisher not initialized. Cannot publish event '%s'", event)
        return

    message = aio_pika.Message(
        body=payload.model_dump_json().encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    
    await _exchange.publish(message, routing_key=event)
    logger.debug("Published event '%s'", event)


async def start_message_consumer(connection: aio_pika.RobustConnection) -> None:
    """Background worker to consume messages from RabbitMQ.
    
    Binds the monolith queue to the exchange for all registered events, and
    routes incoming messages to the correct async handlers.
    """
    channel = await connection.channel()
    # Set prefetch count to prevent overwhelming the worker
    await channel.set_qos(prefetch_count=100)
    
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )

    # Declare Dead Letter Exchange and Queue
    dlx_name = "aparty.dlx"
    await channel.declare_exchange(dlx_name, aio_pika.ExchangeType.FANOUT, durable=True)
    dlq = await channel.declare_queue("aparty.dlq", durable=True)
    await dlq.bind(dlx_name)
    
    # Declare main queue with DLX routing
    queue = await channel.declare_queue(
        QUEUE_NAME, 
        durable=True,
        arguments={
            "x-dead-letter-exchange": dlx_name,
        }
    )
    
    # Bind the queue for every subscribed event
    for event_name in _handlers.keys():
        await queue.bind(exchange, routing_key=event_name)
        logger.info("Bound queue '%s' to routing key '%s'", QUEUE_NAME, event_name)

    logger.info("Started RabbitMQ consumer on queue '%s'", QUEUE_NAME)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            # message.process(requeue=False) automatically sends an ACK on success.
            # On exception, it sends a NACK with requeue=False, which routes the 
            # message to the Dead Letter Exchange (aparty.dlx).
            async with message.process(requeue=False):
                routing_key = message.routing_key or ""
                handlers = _handlers.get(routing_key, [])
                
                if not handlers:
                    continue
                
                try:
                    payload = json.loads(message.body.decode())
                except json.JSONDecodeError as e:
                    logger.error("Failed to decode message body for '%s': %s", routing_key, e)
                    # Raising an exception here triggers the DLX routing
                    raise

                # Fan out to local handlers
                results = await asyncio.gather(
                    *[h(payload) for h in handlers],
                    return_exceptions=True,
                )
                
                has_errors = False
                for handler, result in zip(handlers, results):
                    if isinstance(result, Exception):
                        has_errors = True
                        logger.error(
                            "Handler '%s' failed for event '%s': %s",
                            handler.__qualname__,
                            routing_key,
                            result,
                            exc_info=result,
                        )
                
                if has_errors:
                    # Trigger the DLX routing for application-level handler failures
                    raise RuntimeError(f"One or more handlers failed for event {routing_key}")
