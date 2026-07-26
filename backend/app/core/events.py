"""Lightweight in-process Domain Event Bus.

This replaces direct cross-domain service calls for fire-and-forget scenarios
(e.g. "booking confirmed → send notification to apartment owner").

Design:
  - Zero external dependencies (no Kafka, no Redis Pub/Sub).
  - Subscribers are async coroutines registered at startup via ``subscribe()``.
  - ``publish()`` fans out to all registered handlers concurrently using
    ``asyncio.gather`` so one slow handler never blocks others.
  - Exceptions in individual handlers are logged but never bubble up to callers.
    A failing notification must NEVER roll back a business transaction.

Microservice migration path:
    When the project graduates to microservices, replace ``publish()`` with a
    Redis Streams / Kafka producer and ``subscribe()`` with consumer-group
    registration. Call-sites in services.py remain unchanged.

Example:
    # Publisher (domains/orders/services.py):
    from app.core.events import publish
    await publish("booking.confirmed", {"apartment_id": str(apt_id), ...})

    # Subscriber (registered in domains/users/__init__.py or lifespan):
    from app.core.events import subscribe
    subscribe("booking.confirmed", _handle_booking_confirmed)
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

# Registry: event_name → list[async handler]
_handlers: dict[str, list[Callable[..., Awaitable[Any]]]] = defaultdict(list)


def subscribe(event: str, handler: Callable[..., Awaitable[Any]]) -> None:
    """Register *handler* to be called whenever *event* is published.

    Args:
        event: Dot-namespaced event string, e.g. ``"booking.confirmed"``.
        handler: An async callable accepting a single ``payload: dict`` arg.
    """
    _handlers[event].append(handler)
    logger.debug("Subscribed %s to event '%s'.", handler.__qualname__, event)


async def publish(event: str, payload: dict[str, Any]) -> None:
    """Fan out *payload* to every handler subscribed to *event*.

    Args:
        event: The event name to publish.
        payload: Arbitrary data dict delivered to each subscriber.
    """
    handlers = _handlers.get(event, [])
    if not handlers:
        return

    results = await asyncio.gather(
        *[h(payload) for h in handlers],
        return_exceptions=True,
    )
    for handler, result in zip(handlers, results):
        if isinstance(result, Exception):
            logger.error(
                "Handler '%s' failed for event '%s': %s",
                handler.__qualname__,
                event,
                result,
                exc_info=result,
            )
