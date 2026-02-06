"""Heartbeat publisher — sends periodic heartbeat via {robot_id}.hb."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import aio_pika
from loguru import logger

if TYPE_CHECKING:
    from aio_pika.abc import AbstractExchange

    from src.config import MockSettings
    from src.mq.connection import MQConnection


class HeartbeatPublisher:
    """Publishes periodic heartbeat messages to {robot_id}.hb via the topic exchange."""

    def __init__(self, connection: MQConnection, settings: MockSettings) -> None:
        self._connection = connection
        self._settings = settings
        self._exchange: AbstractExchange | None = None
        self._task: asyncio.Task | None = None
        self._running = False

    async def initialize(self) -> None:
        """Declare the exchange (idempotent) and cache reference."""
        channel = await self._connection.get_channel()
        self._exchange = await channel.declare_exchange(
            self._settings.mq_exchange,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    async def start(self) -> None:
        """Start the heartbeat background task."""
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info("Heartbeat started (interval={}s)", self._settings.heartbeat_interval)

    async def stop(self) -> None:
        """Stop the heartbeat background task gracefully."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Heartbeat stopped")

    async def _heartbeat_loop(self) -> None:
        """Background loop: publish heartbeat at configured interval."""
        while self._running:
            try:
                await self._publish_heartbeat()
            except Exception:
                logger.exception("Failed to publish heartbeat")
            await asyncio.sleep(self._settings.heartbeat_interval)

    async def _publish_heartbeat(self) -> None:
        """Publish a single heartbeat message."""
        from src.schemas.results import HeartbeatMessage

        if self._exchange is None:
            raise RuntimeError("HeartbeatPublisher not initialized. Call initialize() first.")

        msg = HeartbeatMessage(
            robot_id=self._settings.robot_id,
            timestamp=datetime.now(tz=UTC).isoformat(),
        )
        routing_key = f"{self._settings.robot_id}.hb"
        body = msg.model_dump_json().encode()

        await self._exchange.publish(
            aio_pika.Message(
                body=body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,  # heartbeat is ephemeral
            ),
            routing_key=routing_key,
        )
        logger.debug("Heartbeat published via {}", routing_key)
