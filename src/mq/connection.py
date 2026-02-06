"""RabbitMQ connection management for the mock robot server."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aio_pika import connect_robust
from aio_pika.abc import AbstractChannel, AbstractRobustConnection
from loguru import logger

if TYPE_CHECKING:
    from src.config import MockSettings


class MQConnection:
    """Manages a single RabbitMQ connection and channel for the mock server."""

    def __init__(self, settings: MockSettings) -> None:
        self._settings = settings
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None

    @property
    def is_connected(self) -> bool:
        """Check if the underlying connection is open."""
        return self._connection is not None and not self._connection.is_closed

    async def connect(self) -> None:
        """Establish a robust RabbitMQ connection."""
        amqp_url = (
            f"amqp://{self._settings.mq_user}:{self._settings.mq_password}"
            f"@{self._settings.mq_host}:{self._settings.mq_port}{self._settings.mq_vhost}"
        )

        self._connection = await connect_robust(
            amqp_url,
            timeout=self._settings.mq_connection_timeout,
            heartbeat=self._settings.mq_heartbeat,
        )

        logger.info("Connected to RabbitMQ at {}:{}", self._settings.mq_host, self._settings.mq_port)

    async def disconnect(self) -> None:
        """Close channel and connection gracefully."""
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
            self._channel = None

        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            self._connection = None

        logger.info("Disconnected from RabbitMQ")

    async def get_channel(self) -> AbstractChannel:
        """Return existing channel or create a new one from the connection."""
        if self._connection is None or self._connection.is_closed:
            raise RuntimeError("RabbitMQ connection not established. Call connect() first.")

        if self._channel is None or self._channel.is_closed:
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=self._settings.mq_prefetch_count)

        return self._channel
