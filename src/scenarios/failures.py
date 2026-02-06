"""Task-specific failure messages for mock scenarios."""

from __future__ import annotations

import random

from src.schemas.commands import TaskName

# Realistic failure messages per task type
FAILURE_MESSAGES: dict[TaskName, list[str]] = {
    TaskName.SETUP_CARTRIDGES: [
        "Gripper malfunction during cartridge pickup",
        "Cartridge not detected at expected storage position",
        "Silica cartridge alignment failure at work station mount point",
        "Sample cartridge barcode scan failed - cartridge may be misplaced",
    ],
    TaskName.SETUP_TUBE_RACK: [
        "Tube rack not detected at storage location",
        "Gripper force sensor exceeded safe threshold during rack pickup",
        "Tube rack alignment failure at work station",
    ],
    TaskName.COLLAPSE_CARTRIDGES: [
        "Cartridge removal failed - cartridge stuck in mount",
        "Gripper timeout during cartridge return to storage",
        "Storage position occupied - cannot return cartridge",
    ],
    TaskName.TAKE_PHOTO: [
        "Camera focus failure - image quality below threshold",
        "Navigation to photo position failed - path obstructed",
        "Device screen not detected at expected position",
    ],
    TaskName.START_CC: [
        "Column chromatography system not responding to start command",
        "Pressure sensor reading abnormal before start - safety check failed",
        "Solvent level insufficient for configured run duration",
        "System equilibration timeout exceeded",
    ],
    TaskName.TERMINATE_CC: [
        "CC system did not acknowledge terminate command within timeout",
        "Emergency stop triggered during termination sequence",
        "Result screen capture failed during termination",
    ],
    TaskName.FRACTION_CONSOLIDATION: [
        "Round bottom flask not detected at consolidation station",
        "Tube extraction failure at position - tube may be stuck",
        "Flask overflow sensor triggered during consolidation",
    ],
    TaskName.START_EVAPORATION: [
        "Evaporator vacuum pump failed to reach target pressure",
        "Water bath temperature sensor malfunction",
        "Flask rotation motor stalled during ramp-up",
        "Safety interlock triggered - evaporator lid not properly sealed",
    ],
    TaskName.STOP_EVAPORATION: [
        "Flask stuck to evaporator joint - removal failed",
        "Vacuum release valve stuck in closed position",
        "Evaporator lift mechanism jammed during flask retrieval",
        "Water bath drain timeout exceeded",
    ],
    TaskName.SETUP_CCS_BINS: [
        "Bin not found at storage location",
        "Fume hood chute already occupied by another bin",
        "Gripper force sensor exceeded threshold during bin pickup",
        "Bin barcode scan failed - bin may be misplaced",
    ],
    TaskName.RETURN_CCS_BINS: [
        "Bin grip failure during removal from chute",
        "Waste area full - cannot place bin",
        "Bin stuck in chute rail mechanism",
        "Navigation to waste area blocked by obstacle",
    ],
    TaskName.RETURN_CARTRIDGES: [
        "Cartridge stuck in mount - removal failed",
        "Waste receptacle not accessible",
        "Gripper timeout during cartridge return",
        "Silica cartridge barcode mismatch during return",
    ],
    TaskName.RETURN_TUBE_RACK: [
        "Tube rack jammed in work station slot",
        "Path to waste area blocked by equipment",
        "Gripper force sensor exceeded safe threshold during rack removal",
        "Waste area rack slot occupied",
    ],
}

# Error codes: 1010-1099 range for task-specific failures
_ERROR_CODE_BASE: dict[TaskName, int] = {
    TaskName.SETUP_CARTRIDGES: 1010,
    TaskName.SETUP_TUBE_RACK: 1020,
    TaskName.COLLAPSE_CARTRIDGES: 1030,
    TaskName.TAKE_PHOTO: 1040,
    TaskName.START_CC: 1050,
    TaskName.TERMINATE_CC: 1060,
    TaskName.FRACTION_CONSOLIDATION: 1070,
    TaskName.START_EVAPORATION: 1080,
    TaskName.STOP_EVAPORATION: 1090,
    TaskName.SETUP_CCS_BINS: 1100,
    TaskName.RETURN_CCS_BINS: 1110,
    TaskName.RETURN_CARTRIDGES: 1120,
    TaskName.RETURN_TUBE_RACK: 1130,
}


def get_random_failure(task_name: TaskName) -> tuple[int, str]:
    """Get a random failure code and message for the given task type.

    Returns:
        Tuple of (error_code, error_message).
    """
    messages = FAILURE_MESSAGES.get(task_name, ["Unknown task failure"])
    message = random.choice(messages)  # noqa: S311
    base_code = _ERROR_CODE_BASE.get(task_name, 1090)
    # Add small offset based on message index for variety
    code = base_code + random.randint(0, 9)  # noqa: S311
    return code, message
