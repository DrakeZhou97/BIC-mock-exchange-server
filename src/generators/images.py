"""Image URL and CapturedImage generation for mock results.

Generates deterministic mock image URLs with timestamps for device screen captures.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.schemas.results import CapturedImage


def generate_image_url(base_url: str, work_station_id: str, device_id: str, component: str) -> str:
    """Generate a mock image URL with timestamp."""
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    return f"{base_url}/{work_station_id}/{device_id}/{component}/{timestamp}.jpg"


def generate_captured_images(
    base_url: str,
    work_station_id: str,
    device_id: str,
    device_type: str,
    components: list[str] | str,
) -> list[CapturedImage]:
    """Generate CapturedImage list for one or multiple components."""
    if isinstance(components, str):
        components = [components]
    return [
        CapturedImage(
            work_station_id=work_station_id,
            device_id=device_id,
            device_type=device_type,
            component=component,
            url=generate_image_url(base_url, work_station_id, device_id, component),
        )
        for component in components
    ]
