"""Equipment status routes."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter

router = APIRouter()


# Mock equipment status data
MOCK_EQUIPMENT = {
    "plate_reader": {
        "id": "plate_reader_01",
        "name": "SpectraMax M5 Plate Reader",
        "status": "idle",
        "last_calibration": "2026-04-01T08:00:00Z",
        "next_maintenance": "2026-05-01T08:00:00Z",
        "metrics": {
            "temperature": 25.5,
            "humidity": 45.0,
        },
    },
    "pcr_machine": {
        "id": "pcr_machine_01",
        "name": "QuantStudio 7 Pro qPCR",
        "status": "idle",
        "last_calibration": "2026-04-02T10:00:00Z",
        "next_maintenance": "2026-05-02T10:00:00Z",
        "metrics": {
            "blocks_temperature": 22.0,
        },
    },
    "incubator": {
        "id": "incubator_01",
        "name": "CO2 Incubator Sanyo",
        "status": "running",
        "last_calibration": "2026-03-15T09:00:00Z",
        "next_maintenance": "2026-04-15T09:00:00Z",
        "metrics": {
            "temperature": 37.0,
            "co2_level": 5.0,
        },
    },
    "centrifuge": {
        "id": "centrifuge_01",
        "name": "Eppendorf 5424R",
        "status": "idle",
        "last_calibration": "2026-03-20T14:00:00Z",
        "next_maintenance": "2026-04-20T14:00:00Z",
        "metrics": {
            "temperature": 4.0,
        },
    },
    "pipetting_robot": {
        "id": "pipetting_robot_01",
        "name": "Hamilton STARlet",
        "status": "idle",
        "last_calibration": "2026-04-03T11:00:00Z",
        "next_maintenance": "2026-05-03T11:00:00Z",
        "metrics": {},
    },
}


@router.get("/status", response_model=dict[str, Any])
async def get_equipment_status() -> dict[str, Any]:
    """Get status of all equipment.

    Returns:
        Dictionary containing equipment status information for all devices.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "equipment": MOCK_EQUIPMENT,
    }


@router.get("/{equipment_id}", response_model=dict[str, Any])
async def get_equipment_by_id(equipment_id: str) -> dict[str, Any]:
    """Get status of specific equipment by ID.

    Args:
        equipment_id: Unique equipment identifier.

    Returns:
        Equipment status details.

    Raises:
        HTTPException: If equipment not found.
    """
    if equipment_id not in MOCK_EQUIPMENT:
        raise HTTPException(status_code=404, detail="Equipment not found")

    return MOCK_EQUIPMENT[equipment_id]
