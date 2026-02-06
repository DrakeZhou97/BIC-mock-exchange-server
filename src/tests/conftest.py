"""Shared fixtures for src tests."""

from __future__ import annotations

import pytest

from src.config import MockSettings


@pytest.fixture
def mock_settings() -> MockSettings:
    """Default settings for testing."""
    return MockSettings(
        mq_host="localhost",
        mq_port=5672,
        mq_exchange="test_exchange",
        base_delay_multiplier=0.01,  # Very fast for tests
        min_delay_seconds=0.0,
        default_scenario="success",
        failure_rate=0.0,
        timeout_rate=0.0,
        image_base_url="http://test:9000/mock-images",
        robot_id="test-robot-001",
        log_level="DEBUG",
        heartbeat_interval=1.0,  # Faster for tests
    )
