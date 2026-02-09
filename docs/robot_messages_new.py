"""
Robot message types for BIC laboratory automation.

Message definitions for communication between agent service and robot
via message queue. Includes task commands and result messages for:
- Cartridge and tube rack setup
- Column chromatography (CC) operations
- Rotary evaporation (RE) operations
- Photo capture
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


# region Enums
class TaskName(StrEnum):
    """Robot task command names."""

    SETUP_CARTRIDGES = "setup_tubes_to_column_machine"
    SETUP_TUBE_RACK = "setup_tube_rack"
    COLLAPSE_CARTRIDGES = "collapse_cartridges"
    TAKE_PHOTO = "take_photo"
    START_CC = "start_column_chromatography"
    TERMINATE_CC = "terminate_column_chromatography"
    FRACTION_CONSOLIDATION = "fraction_consolidation"
    START_EVAPORATION = "start_evaporation"


class RobotState(StrEnum):
    """Robot operational states."""

    IDLE = "idle"
    WAIT_FOR_SCREEN_MANIPULATION = "wait_for_screen_manipulation"
    WATCH_COLUMN_MACHINE_SCREEN = "watch_column_machine_screen"
    MOVING_WITH_ROUND_BOTTOM_FLASK = "moving_with_round_bottom_flask"
    OBSERVE_EVAPORATION = "observe_evaporation"


class EntityState(StrEnum):
    """Common entity states."""

    MOUNTED = "mounted"
    USING = "using"
    USED = "used"
    RUNNING = "running"
    TERMINATED = "terminated"
    EVAPORATING = "evaporating"


class PeakGatheringMode(StrEnum):
    """Peak collection modes for column chromatography."""

    ALL = "all"
    PEAK = "peak"
    NONE = "none"


class BinState(StrEnum):
    """Waste bin states."""

    OPEN = "open"
    CLOSE = "close"
    FULL = "full"


# endregion


# region Messages
class RobotCommand[P: BaseModel](BaseModel):
    """Command message sent to robot via MQ."""

    task_id: str
    task_name: TaskName
    params: P


class RobotResult(BaseModel):
    """Result message received from robot via MQ."""

    code: int
    msg: str
    task_id: str
    updates: list["EntityUpdate"] = Field(default_factory=list)
    images: list["CapturedImage"] | None = None


# endregion


# region Command Parameters
class SetupCartridgesParams(BaseModel):
    silica_cartridge_location_id: str
    silica_cartridge_type: str
    silica_cartridge_id: str
    sample_cartridge_location_id: str
    sample_cartridge_type: str
    sample_cartridge_id: str
    work_station_id: str


class SetupTubeRackParams(BaseModel):
    tube_rack_location_id: str
    work_station_id: str
    end_state: RobotState = RobotState.IDLE


class CollapseCartridgesParams(BaseModel):
    work_station_id: str
    silica_cartridge_id: str
    sample_cartridge_id: str
    end_state: RobotState = RobotState.IDLE


class TakePhotoParams(BaseModel):
    work_station_id: str
    device_id: str
    device_type: str
    components: list[str] | str
    end_state: RobotState


class StartCCParams(BaseModel):
    work_station_id: str
    device_id: str
    device_type: str
    experiment_params: "CCExperimentParams"
    end_state: RobotState


class TerminateCCParams(BaseModel):
    work_station_id: str
    device_id: str
    device_type: str
    end_state: RobotState


class FractionConsolidationParams(BaseModel):
    work_station_id: str
    device_id: str
    device_type: str
    collect_config: list[int] = Field(description="1=collect, 0=discard per tube")
    end_state: RobotState


class StartEvaporationParams(BaseModel):
    work_station_id: str
    device_id: str
    device_type: str
    profiles: "EvaporationProfiles"
    post_run_state: RobotState


class CapturedImage(BaseModel):
    """Captured image metadata."""

    work_station_id: str
    device_id: str
    device_type: str
    component: str
    url: str


# Concrete command types
SetupCartridgesCommand = RobotCommand[SetupCartridgesParams]
SetupTubeRackCommand = RobotCommand[SetupTubeRackParams]
CollapseCartridgesCommand = RobotCommand[CollapseCartridgesParams]
TakePhotoCommand = RobotCommand[TakePhotoParams]
StartCCCommand = RobotCommand[StartCCParams]
TerminateCCCommand = RobotCommand[TerminateCCParams]
FractionConsolidationCommand = RobotCommand[FractionConsolidationParams]
StartEvaporationCommand = RobotCommand[StartEvaporationParams]


# endregion


# region Experiment Parameters
class CCExperimentParams(BaseModel):
    """Column chromatography experiment parameters."""

    silicone_column: str = Field(description="Silica column spec, e.g. '40g'")
    peak_gathering_mode: PeakGatheringMode
    air_clean_minutes: int = Field(description="Air purge duration in minutes")
    run_minutes: int = Field(description="Total run duration in minutes")
    need_equilibration: bool = Field(description="Whether column equilibration needed")
    left_rack: str | None = Field(default=None, description="Left tube rack spec")
    right_rack: str | None = Field(default=None, description="Right tube rack spec")


class EvaporationTrigger(BaseModel):
    """Trigger condition for evaporation profile changes."""

    type: Literal["time_from_start", "event"]
    time_in_sec: int | None = Field(default=None, description="Delay in seconds")
    event_name: str | None = Field(
        default=None,
        description="Event name for event trigger",
    )


class EvaporationProfile(BaseModel):
    """Evaporation parameter profile."""

    lower_height: float = Field(description="Flask lowering height in mm")
    rpm: int = Field(description="Rotation speed in rpm")
    target_temperature: float = Field(description="Water bath temp in Celsius")
    target_pressure: float = Field(description="Vacuum pressure in mbar")
    trigger: EvaporationTrigger | None = Field(default=None)


class EvaporationProfiles(BaseModel):
    """Collection of evaporation profiles for different stages."""

    start: EvaporationProfile = Field(description="Initial profile (required)")
    stop: EvaporationProfile | None = Field(default=None)
    lower_pressure: EvaporationProfile | None = Field(default=None)
    reduce_bumping: EvaporationProfile | None = Field(
        default=None,
        description="Anti-bumping safety",
    )


# endregion


# region Entity Properties
class RobotProperties(BaseModel):
    """Robot entity properties."""

    location: str
    state: RobotState


class CartridgeProperties(BaseModel):
    """Cartridge (silica/sample) properties."""

    location: str
    state: EntityState


class TubeRackProperties(BaseModel):
    """Tube rack properties."""

    location: str
    state: str  # Compound states like "used,pulled_out,ready_for_recovery"


class RoundBottomFlaskProperties(BaseModel):
    """Round bottom flask properties."""

    location: str
    state: str  # Compound states like "used,evaporating"


class CCSExtModuleProperties(BaseModel):
    """CC external module properties."""

    state: EntityState


class CCSystemProperties(BaseModel):
    """Column chromatography system properties."""

    state: EntityState
    experiment_params: CCExperimentParams | None = None
    start_timestamp: str | None = None


class EvaporatorProperties(BaseModel):
    """Evaporator properties."""

    running: bool
    lower_height: float
    rpm: int
    target_temperature: float
    current_temperature: float
    target_pressure: float
    current_pressure: float


class PCCChuteProperties(BaseModel):
    """Post-column-chromatography chute properties."""

    pulled_out_mm: float
    pulled_out_rate: float
    closed: bool
    front_waste_bin: BinState | None
    back_waste_bin: BinState | None


# endregion


# region Entity Updates
class RobotUpdate(BaseModel):
    type: Literal["robot"] = "robot"
    id: str
    properties: RobotProperties


class SilicaCartridgeUpdate(BaseModel):
    type: Literal["silica_cartridge"] = "silica_cartridge"
    id: str
    properties: CartridgeProperties


class SampleCartridgeUpdate(BaseModel):
    type: Literal["sample_cartridge"] = "sample_cartridge"
    id: str
    properties: CartridgeProperties


class TubeRackUpdate(BaseModel):
    type: Literal["tube_rack"] = "tube_rack"
    id: str
    properties: TubeRackProperties


class RoundBottomFlaskUpdate(BaseModel):
    type: Literal["round_bottom_flask"] = "round_bottom_flask"
    id: str
    properties: RoundBottomFlaskProperties


class CCSExtModuleUpdate(BaseModel):
    type: Literal["ccs_ext_module"] = "ccs_ext_module"
    id: str
    properties: CCSExtModuleProperties


class CCSystemUpdate(BaseModel):
    type: Literal["column_chromatography_system", "isco_combiflash_nextgen_300"]
    id: str
    properties: CCSystemProperties


class EvaporatorUpdate(BaseModel):
    type: Literal["evaporator"] = "evaporator"
    id: str
    properties: EvaporatorProperties


class PCCLeftChuteUpdate(BaseModel):
    type: Literal["pcc_left_chute"] = "pcc_left_chute"
    id: str
    properties: PCCChuteProperties


class PCCRightChuteUpdate(BaseModel):
    type: Literal["pcc_right_chute"] = "pcc_right_chute"
    id: str
    properties: PCCChuteProperties


EntityUpdate = Annotated[
    RobotUpdate
    | SilicaCartridgeUpdate
    | SampleCartridgeUpdate
    | TubeRackUpdate
    | RoundBottomFlaskUpdate
    | CCSExtModuleUpdate
    | CCSystemUpdate
    | EvaporatorUpdate
    | PCCLeftChuteUpdate
    | PCCRightChuteUpdate,
    Field(discriminator="type"),
]


# endregion
