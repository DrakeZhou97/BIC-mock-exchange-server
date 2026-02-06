"""Simulator for take_photo task."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from src.generators.entity_updates import create_robot_update
from src.generators.images import generate_captured_images
from src.schemas.commands import TaskName
from src.schemas.results import EntityUpdate, RobotResult
from src.simulators.base import BaseSimulator

if TYPE_CHECKING:
    from pydantic import BaseModel

    from src.schemas.commands import TakePhotoParams


class PhotoSimulator(BaseSimulator):
    """Handles take_photo task."""

    async def simulate(self, task_id: str, task_name: TaskName, params: BaseModel) -> RobotResult:
        if task_name != TaskName.TAKE_PHOTO:
            raise ValueError(f"PhotoSimulator cannot handle task: {task_name}")
        return await self._simulate_take_photo(task_id, params)  # type: ignore[arg-type]

    async def _simulate_take_photo(self, task_id: str, params: TakePhotoParams) -> RobotResult:
        """Simulate take_photo: 2-5s per component."""
        components = params.components if isinstance(params.components, list) else [params.components]
        logger.info("Simulating take_photo for task {} ({} components)", task_id, len(components))

        # Log: robot arrived at station
        await self._publish_log(task_id, [
            create_robot_update(self.robot_id, params.work_station_id, params.end_state),
        ], "robot arrived at station")

        # Delay scales with number of components
        await self._apply_delay(2.0 * len(components), 5.0 * len(components))

        # Log: per-component photo taken
        for component in components:
            await self._publish_log(task_id, [
                create_robot_update(self.robot_id, params.work_station_id, params.end_state),
            ], f"photo taken for {component}")

        updates: list[EntityUpdate] = [
            create_robot_update(self.robot_id, params.work_station_id, params.end_state),
        ]

        images = generate_captured_images(
            self.image_base_url, params.work_station_id, params.device_id, params.device_type, components
        )

        return RobotResult(code=0, msg="take_photo completed", task_id=task_id, updates=updates, images=images)
