"""Result producer — publishes RobotResult messages to the topic exchange."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import aio_pika
from loguru import logger

if TYPE_CHECKING:
    from aio_pika.abc import AbstractExchange

    from src.config import MockSettings
    from src.mq.connection import MQConnection
    from src.schemas.results import EntityUpdate, RobotResult


class ResultProducer:
    """Publishes simulation results via the topic exchange with per-robot routing keys."""

    def __init__(self, connection: MQConnection, settings: MockSettings) -> None:
        self._connection = connection
        self._settings = settings
        self._exchange: AbstractExchange | None = None

    async def initialize(self) -> None:
        """Declare the topic exchange (idempotent) and cache a reference."""
        channel = await self._connection.get_channel()
        self._exchange = await channel.declare_exchange(
            self._settings.mq_exchange,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("Producer initialized, exchange: {}", self._settings.mq_exchange)

    async def publish_result(self, result: RobotResult) -> None:
        """Serialize and publish a RobotResult to the exchange with routing key <robot_id>.result."""
        if self._exchange is None:
            raise RuntimeError("Producer not initialized. Call initialize() first.")

        routing_key = f"{self._settings.robot_id}.result"
        body = result.model_dump_json().encode()

        await self._exchange.publish(
            aio_pika.Message(
                body=body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )

        logger.info(
            "Published result for task {} (code={}) via {}: {}",
            result.task_id,
            result.code,
            routing_key,
            result.model_dump_json(indent=2),
        )

    async def publish_intermediate_update(self, task_id: str, updates: Sequence[EntityUpdate]) -> None:
        """Publish an intermediate entity-update message via the log channel.

        Intermediate updates are state changes that occur during long-running tasks
        (e.g., CC running, evaporation progress). They should be published to the
        log channel ({robot_id}.log), NOT the result channel, so the lab service
        processes them as real-time state updates without affecting task completion status.
        """
        from src.schemas.results import LogMessage as _LogMessage

        if self._exchange is None:
            raise RuntimeError("Producer not initialized. Call initialize() first.")

        from src.generators.entity_updates import generate_robot_timestamp

        log_msg = _LogMessage(
            task_id=task_id,
            updates=list(updates),
            timestamp=generate_robot_timestamp(),
        )

        routing_key = f"{self._settings.robot_id}.log"
        body = log_msg.model_dump_json().encode()

        await self._exchange.publish(
            aio_pika.Message(
                body=body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )

        logger.debug("Published intermediate update via log channel for task {}", task_id)
