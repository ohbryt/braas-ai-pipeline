"""
BRaaS Event Bus System
=======================

Asynchronous event bus for pipeline stage communication. Supports
publish/subscribe patterns with typed events, filtering, and
correlation ID propagation for experiment tracing.

Usage:
    bus = EventBus()
    bus.subscribe("experiment.started", my_handler)
    await bus.publish(Event(topic="experiment.started", data={...}))
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

# Type alias for event handler functions
EventHandler = Callable[["Event"], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Event:
    """Immutable event object for pipeline communication.

    Attributes:
        topic: Dot-separated event topic (e.g. 'experiment.status.changed').
        data: Arbitrary payload data.
        event_id: Unique identifier for this event instance.
        correlation_id: Shared ID linking related events in a workflow.
        experiment_id: Associated experiment, if applicable.
        timestamp: Unix timestamp of event creation.
        source: Identifier of the component that emitted the event.
    """

    topic: str
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    correlation_id: str | None = None
    experiment_id: str | None = None
    timestamp: float = field(default_factory=time.time)
    source: str = ""


@dataclass
class _Subscription:
    """Internal subscription record."""

    handler: EventHandler
    topic_pattern: str
    subscription_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    active: bool = True


class EventBus:
    """Async event bus with topic-based pub/sub and wildcard matching.

    Supports exact topic matches and wildcard patterns:
      - 'experiment.started' matches only that exact topic
      - 'experiment.*' matches any topic starting with 'experiment.'
      - '*' matches all topics

    Thread-safety: This class is designed for use within a single
    asyncio event loop. For cross-thread usage, wrap calls with
    loop.call_soon_threadsafe or asyncio.run_coroutine_threadsafe.
    """

    def __init__(self) -> None:
        self._subscriptions: dict[str, list[_Subscription]] = {}
        self._history: list[Event] = []
        self._max_history: int = 1000
        self._lock = asyncio.Lock()
        self._middleware: list[Callable[[Event], Awaitable[Event | None]]] = []

    def subscribe(
        self,
        topic_pattern: str,
        handler: EventHandler,
    ) -> str:
        """Register a handler for events matching the given topic pattern.

        Args:
            topic_pattern: Topic string or wildcard pattern.
            handler: Async callable that receives an Event.

        Returns:
            Subscription ID that can be used to unsubscribe.
        """
        sub = _Subscription(handler=handler, topic_pattern=topic_pattern)
        if topic_pattern not in self._subscriptions:
            self._subscriptions[topic_pattern] = []
        self._subscriptions[topic_pattern].append(sub)
        logger.debug(
            "Subscribed handler %s to topic '%s' (sub_id=%s)",
            handler.__qualname__,
            topic_pattern,
            sub.subscription_id,
        )
        return sub.subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription by its ID.

        Args:
            subscription_id: The ID returned by subscribe().

        Returns:
            True if the subscription was found and removed.
        """
        for pattern, subs in self._subscriptions.items():
            for sub in subs:
                if sub.subscription_id == subscription_id:
                    sub.active = False
                    subs.remove(sub)
                    logger.debug(
                        "Unsubscribed %s from topic '%s'",
                        subscription_id,
                        pattern,
                    )
                    return True
        return False

    async def publish(self, event: Event) -> int:
        """Publish an event to all matching subscribers.

        Runs middleware pipeline first, then dispatches to handlers.
        Handlers are invoked concurrently via asyncio.gather.

        Args:
            event: The event to publish.

        Returns:
            Number of handlers that were invoked.

        Raises:
            Exception: Re-raises if a handler fails (after logging).
        """
        # Run middleware chain
        processed_event: Event | None = event
        for mw in self._middleware:
            if processed_event is None:
                logger.debug("Event %s filtered out by middleware", event.event_id)
                return 0
            processed_event = await mw(processed_event)
        if processed_event is None:
            return 0
        event = processed_event

        # Record in history
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history :]

        # Collect matching handlers
        handlers: list[EventHandler] = []
        for pattern, subs in self._subscriptions.items():
            if self._matches(pattern, event.topic):
                for sub in subs:
                    if sub.active:
                        handlers.append(sub.handler)

        if not handlers:
            logger.debug(
                "No handlers for event topic '%s' (event_id=%s)",
                event.topic,
                event.event_id,
            )
            return 0

        # Dispatch to all handlers concurrently
        results = await asyncio.gather(
            *(h(event) for h in handlers),
            return_exceptions=True,
        )

        # Log any handler exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "Handler %s raised exception for event %s: %s",
                    handlers[i].__qualname__,
                    event.event_id,
                    result,
                    exc_info=result,
                )

        return len(handlers)

    def add_middleware(
        self, middleware: Callable[[Event], Awaitable[Event | None]]
    ) -> None:
        """Add a middleware function to the event processing pipeline.

        Middleware receives an event and returns a (possibly modified) event,
        or None to filter/drop the event.

        Args:
            middleware: Async callable that transforms or filters events.
        """
        self._middleware.append(middleware)

    @staticmethod
    def _matches(pattern: str, topic: str) -> bool:
        """Check if a topic matches a subscription pattern.

        Supports:
            - Exact match: 'a.b.c' matches 'a.b.c'
            - Wildcard suffix: 'a.*' matches 'a.b', 'a.b.c'
            - Global wildcard: '*' matches everything
        """
        if pattern == "*":
            return True
        if pattern == topic:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return topic == prefix or topic.startswith(prefix + ".")
        return False

    @property
    def history(self) -> list[Event]:
        """Read-only access to recent event history."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear the event history buffer."""
        self._history.clear()

    @property
    def subscription_count(self) -> int:
        """Total number of active subscriptions."""
        return sum(
            len([s for s in subs if s.active])
            for subs in self._subscriptions.values()
        )


# Module-level singleton for convenience
_default_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get or create the default global EventBus singleton."""
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


def reset_event_bus() -> None:
    """Reset the global EventBus singleton (primarily for testing)."""
    global _default_bus
    _default_bus = None
