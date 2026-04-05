"""
BRaaS Robot Drivers - Abstract and concrete instrument drivers.

Implements a SiLA2-inspired command pattern for lab instrument control.
Provides drivers for liquid handlers, plate readers, thermocyclers,
incubators, and robotic arms, plus a central DriverRegistry.
"""
from __future__ import annotations

import abc
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Type

from braas.core.enums import EquipmentStatus, EquipmentType

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """SiLA2-style command execution status."""
    ACCEPTED = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class CommandResult:
    """Result of a driver command execution."""
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: CommandStatus = CommandStatus.COMPLETED
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0

    @property
    def success(self) -> bool:
        return self.status == CommandStatus.COMPLETED


@dataclass
class CalibrationReport:
    """Report from an instrument calibration procedure."""
    instrument_id: str = ""
    calibration_type: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    passed: bool = True
    measurements: Dict[str, float] = field(default_factory=dict)
    deviations: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class RobotDriver(abc.ABC):
    """
    Abstract base class for all instrument drivers.

    Follows SiLA2-style patterns:
    - Unobservable commands: execute_command() -> immediate result
    - Observable commands: start_command() -> command_id, poll for completion
    - Properties: get_status(), get_properties()
    """

    def __init__(
        self,
        instrument_id: str,
        name: str,
        equipment_type: EquipmentType,
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.instrument_id = instrument_id
        self.name = name
        self.equipment_type = equipment_type
        self.connection_config = connection_config or {}
        self._connected = False
        self._status = EquipmentStatus.OFFLINE
        self._command_history: List[CommandResult] = []
        self._properties: Dict[str, Any] = {}

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def status(self) -> EquipmentStatus:
        return self._status

    @abc.abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the instrument.

        Returns:
            True if connection successful.
        """
        ...

    @abc.abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the instrument."""
        ...

    @abc.abstractmethod
    async def execute_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> CommandResult:
        """
        Execute a command on the instrument.

        Args:
            command: Command name (instrument-specific).
            parameters: Command parameters.

        Returns:
            CommandResult with execution status and data.
        """
        ...

    @abc.abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current instrument status and properties.

        Returns:
            Dict with status information.
        """
        ...

    @abc.abstractmethod
    async def calibrate(self, calibration_type: str = "full") -> CalibrationReport:
        """
        Run calibration procedure on the instrument.

        Args:
            calibration_type: Type of calibration (full, quick, specific).

        Returns:
            CalibrationReport with results.
        """
        ...

    async def reset(self) -> CommandResult:
        """Reset the instrument to its default state."""
        logger.info(f"Resetting {self.name} ({self.instrument_id})")
        return await self.execute_command("reset")

    def _record_command(self, result: CommandResult) -> None:
        """Record a command result in history."""
        self._command_history.append(result)
        if len(self._command_history) > 1000:
            self._command_history = self._command_history[-500:]


class LiquidHandlerDriver(RobotDriver):
    """
    Driver for automated liquid handling systems.

    Supports pipetting operations: aspirate, dispense, mix, transfer,
    serial dilution, and tip management.
    """

    SUPPORTED_COMMANDS = {
        "aspirate", "dispense", "mix", "transfer", "serial_dilute",
        "pick_up_tips", "drop_tips", "move_to", "home", "reset",
    }

    def __init__(
        self,
        instrument_id: str,
        name: str = "Liquid Handler",
        connection_config: Optional[Dict[str, Any]] = None,
        num_channels: int = 8,
        volume_range: tuple = (0.5, 1000.0),
    ) -> None:
        super().__init__(
            instrument_id, name, EquipmentType.LIQUID_HANDLER, connection_config
        )
        self.num_channels = num_channels
        self.volume_range = volume_range  # (min_uL, max_uL)
        self._tip_loaded = False
        self._current_position = {"x": 0, "y": 0, "z": 0}
        self._deck_layout: Dict[str, str] = {}

    async def connect(self) -> bool:
        logger.info(f"Connecting to liquid handler: {self.name}")
        await asyncio.sleep(0.1)  # Simulate connection
        self._connected = True
        self._status = EquipmentStatus.AVAILABLE
        self._properties = {
            "channels": self.num_channels,
            "min_volume_uL": self.volume_range[0],
            "max_volume_uL": self.volume_range[1],
            "firmware_version": "2.4.1",
        }
        logger.info(f"Connected to {self.name}: {self.num_channels} channels")
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        self._status = EquipmentStatus.OFFLINE
        logger.info(f"Disconnected from {self.name}")
        return True

    async def execute_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> CommandResult:
        params = parameters or {}

        if command not in self.SUPPORTED_COMMANDS:
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Unknown command: {command}",
            )

        if not self._connected:
            return CommandResult(
                status=CommandStatus.FAILED,
                error="Not connected to instrument",
            )

        start = datetime.utcnow()
        result = CommandResult(status=CommandStatus.RUNNING, started_at=start)

        try:
            if command == "aspirate":
                volume = params.get("volume_uL", 100.0)
                well = params.get("well", "A1")
                if not self._tip_loaded:
                    result.status = CommandStatus.FAILED
                    result.error = "No tip loaded - pick up tips first"
                elif not (self.volume_range[0] <= volume <= self.volume_range[1]):
                    result.status = CommandStatus.FAILED
                    result.error = (
                        f"Volume {volume} uL outside range "
                        f"{self.volume_range[0]}-{self.volume_range[1]} uL"
                    )
                else:
                    await asyncio.sleep(0.05)
                    result.status = CommandStatus.COMPLETED
                    result.data = {
                        "volume_aspirated_uL": volume,
                        "well": well,
                        "channels_used": min(
                            params.get("channels", 1), self.num_channels
                        ),
                    }

            elif command == "dispense":
                volume = params.get("volume_uL", 100.0)
                well = params.get("well", "A1")
                await asyncio.sleep(0.05)
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "volume_dispensed_uL": volume,
                    "well": well,
                }

            elif command == "mix":
                volume = params.get("volume_uL", 100.0)
                cycles = params.get("cycles", 3)
                await asyncio.sleep(0.05 * cycles)
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "volume_uL": volume,
                    "cycles": cycles,
                    "speed": params.get("speed", "normal"),
                }

            elif command == "transfer":
                volume = params.get("volume_uL", 100.0)
                source = params.get("source", "A1")
                dest = params.get("destination", "B1")
                await asyncio.sleep(0.1)
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "volume_uL": volume,
                    "source": source,
                    "destination": dest,
                }

            elif command == "serial_dilute":
                volume = params.get("volume_uL", 100.0)
                dilution_factor = params.get("dilution_factor", 2)
                num_dilutions = params.get("num_dilutions", 8)
                await asyncio.sleep(0.05 * num_dilutions)
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "volume_uL": volume,
                    "dilution_factor": dilution_factor,
                    "num_dilutions": num_dilutions,
                    "final_dilution": dilution_factor ** num_dilutions,
                }

            elif command == "pick_up_tips":
                tip_rack = params.get("rack", "tip_rack_1")
                await asyncio.sleep(0.05)
                self._tip_loaded = True
                result.status = CommandStatus.COMPLETED
                result.data = {"rack": tip_rack, "tips_loaded": True}

            elif command == "drop_tips":
                await asyncio.sleep(0.03)
                self._tip_loaded = False
                result.status = CommandStatus.COMPLETED
                result.data = {"tips_dropped": True}

            elif command == "home":
                await asyncio.sleep(0.2)
                self._current_position = {"x": 0, "y": 0, "z": 0}
                result.status = CommandStatus.COMPLETED
                result.data = {"position": self._current_position}

            elif command == "reset":
                await asyncio.sleep(0.3)
                self._tip_loaded = False
                self._current_position = {"x": 0, "y": 0, "z": 0}
                result.status = CommandStatus.COMPLETED

        except Exception as e:
            result.status = CommandStatus.FAILED
            result.error = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = (
            result.completed_at - result.started_at
        ).total_seconds() * 1000
        self._record_command(result)
        return result

    async def get_status(self) -> Dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "name": self.name,
            "connected": self._connected,
            "status": self._status.value,
            "tip_loaded": self._tip_loaded,
            "position": self._current_position,
            "channels": self.num_channels,
            "volume_range_uL": self.volume_range,
            "commands_executed": len(self._command_history),
        }

    async def calibrate(self, calibration_type: str = "full") -> CalibrationReport:
        logger.info(f"Calibrating {self.name}: {calibration_type}")
        self._status = EquipmentStatus.CALIBRATING
        await asyncio.sleep(0.2)

        # Simulate calibration measurements
        import random
        rng = random.Random(42)

        report = CalibrationReport(
            instrument_id=self.instrument_id,
            calibration_type=calibration_type,
            passed=True,
            measurements={
                "x_accuracy_mm": 0.05 + rng.gauss(0, 0.01),
                "y_accuracy_mm": 0.05 + rng.gauss(0, 0.01),
                "z_accuracy_mm": 0.03 + rng.gauss(0, 0.005),
                "volume_cv_pct": 1.2 + rng.gauss(0, 0.3),
                "channel_uniformity_pct": 98.5 + rng.gauss(0, 0.5),
            },
            deviations={
                "x_offset_mm": rng.gauss(0, 0.02),
                "y_offset_mm": rng.gauss(0, 0.02),
            },
        )

        if report.measurements.get("volume_cv_pct", 0) > 3.0:
            report.passed = False
            report.recommendations.append(
                "Volume CV exceeds 3% - inspect piston seals"
            )

        self._status = EquipmentStatus.AVAILABLE
        return report


class PlateReaderDriver(RobotDriver):
    """
    Driver for microplate readers.

    Supports absorbance, fluorescence, and luminescence measurements.
    """

    SUPPORTED_COMMANDS = {
        "read_absorbance", "read_fluorescence", "read_luminescence",
        "shake", "set_temperature", "home", "reset",
    }

    def __init__(
        self,
        instrument_id: str,
        name: str = "Plate Reader",
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            instrument_id, name, EquipmentType.PLATE_READER, connection_config
        )
        self._temperature: float = 25.0
        self._plate_inserted = False

    async def connect(self) -> bool:
        logger.info(f"Connecting to plate reader: {self.name}")
        await asyncio.sleep(0.1)
        self._connected = True
        self._status = EquipmentStatus.AVAILABLE
        self._properties = {
            "absorbance_range_nm": (200, 1000),
            "fluorescence_excitation_nm": (230, 900),
            "fluorescence_emission_nm": (280, 900),
            "temperature_range_C": (25, 45),
            "plate_formats": [96, 384],
        }
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        self._status = EquipmentStatus.OFFLINE
        return True

    async def execute_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> CommandResult:
        params = parameters or {}
        if command not in self.SUPPORTED_COMMANDS:
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Unknown command: {command}",
            )
        if not self._connected:
            return CommandResult(
                status=CommandStatus.FAILED,
                error="Not connected",
            )

        start = datetime.utcnow()
        result = CommandResult(started_at=start)

        try:
            if command == "read_absorbance":
                wavelength = params.get("wavelength_nm", 450)
                plate_format = params.get("plate_format", 96)
                await asyncio.sleep(0.2)

                import random
                rng = random.Random(wavelength)
                readings = {
                    f"{chr(65 + r)}{c + 1}": round(rng.uniform(0.05, 2.5), 4)
                    for r in range(8 if plate_format == 96 else 16)
                    for c in range(12 if plate_format == 96 else 24)
                }

                result.status = CommandStatus.COMPLETED
                result.data = {
                    "wavelength_nm": wavelength,
                    "plate_format": plate_format,
                    "readings": readings,
                    "mean_od": round(sum(readings.values()) / len(readings), 4),
                    "temperature_C": self._temperature,
                }

            elif command == "read_fluorescence":
                ex_nm = params.get("excitation_nm", 485)
                em_nm = params.get("emission_nm", 528)
                await asyncio.sleep(0.3)

                import random
                rng = random.Random(ex_nm + em_nm)
                readings = {
                    f"{chr(65 + r)}{c + 1}": round(rng.uniform(100, 50000), 1)
                    for r in range(8)
                    for c in range(12)
                }

                result.status = CommandStatus.COMPLETED
                result.data = {
                    "excitation_nm": ex_nm,
                    "emission_nm": em_nm,
                    "readings": readings,
                    "gain": params.get("gain", 100),
                }

            elif command == "read_luminescence":
                await asyncio.sleep(0.5)
                import random
                rng = random.Random(99)
                readings = {
                    f"{chr(65 + r)}{c + 1}": round(rng.uniform(0, 100000), 1)
                    for r in range(8)
                    for c in range(12)
                }
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "readings": readings,
                    "integration_time_ms": params.get("integration_time_ms", 1000),
                }

            elif command == "set_temperature":
                target = params.get("temperature_C", 37.0)
                await asyncio.sleep(0.1)
                self._temperature = target
                result.status = CommandStatus.COMPLETED
                result.data = {"temperature_C": target}

            elif command == "shake":
                duration_s = params.get("duration_s", 10)
                speed_rpm = params.get("speed_rpm", 300)
                await asyncio.sleep(0.1)
                result.status = CommandStatus.COMPLETED
                result.data = {"duration_s": duration_s, "speed_rpm": speed_rpm}

            elif command in ("home", "reset"):
                await asyncio.sleep(0.2)
                result.status = CommandStatus.COMPLETED

        except Exception as e:
            result.status = CommandStatus.FAILED
            result.error = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = (
            result.completed_at - result.started_at
        ).total_seconds() * 1000
        self._record_command(result)
        return result

    async def get_status(self) -> Dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "name": self.name,
            "connected": self._connected,
            "status": self._status.value,
            "temperature_C": self._temperature,
            "plate_inserted": self._plate_inserted,
        }

    async def calibrate(self, calibration_type: str = "full") -> CalibrationReport:
        logger.info(f"Calibrating {self.name}: {calibration_type}")
        self._status = EquipmentStatus.CALIBRATING
        await asyncio.sleep(0.3)

        report = CalibrationReport(
            instrument_id=self.instrument_id,
            calibration_type=calibration_type,
            passed=True,
            measurements={
                "absorbance_accuracy": 0.003,
                "absorbance_precision_cv": 0.5,
                "wavelength_accuracy_nm": 0.8,
                "temperature_accuracy_C": 0.3,
            },
        )
        self._status = EquipmentStatus.AVAILABLE
        return report


class ThermocyclerDriver(RobotDriver):
    """
    Driver for PCR thermocyclers.

    Supports thermal cycling programs, lid temperature control,
    and real-time monitoring.
    """

    SUPPORTED_COMMANDS = {
        "run_program", "set_temperature", "set_lid_temperature",
        "open_lid", "close_lid", "pause", "resume", "abort",
        "home", "reset",
    }

    def __init__(
        self,
        instrument_id: str,
        name: str = "Thermocycler",
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            instrument_id, name, EquipmentType.THERMOCYCLER, connection_config
        )
        self._block_temperature: float = 25.0
        self._lid_temperature: float = 25.0
        self._lid_open = True
        self._running_program: Optional[str] = None

    async def connect(self) -> bool:
        logger.info(f"Connecting to thermocycler: {self.name}")
        await asyncio.sleep(0.1)
        self._connected = True
        self._status = EquipmentStatus.AVAILABLE
        self._properties = {
            "block_temp_range_C": (4, 100),
            "lid_temp_range_C": (37, 110),
            "ramp_rate_C_per_s": 3.0,
            "sample_capacity": 96,
        }
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        self._status = EquipmentStatus.OFFLINE
        return True

    async def execute_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> CommandResult:
        params = parameters or {}
        if command not in self.SUPPORTED_COMMANDS:
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Unknown command: {command}",
            )
        if not self._connected:
            return CommandResult(
                status=CommandStatus.FAILED,
                error="Not connected",
            )

        start = datetime.utcnow()
        result = CommandResult(started_at=start)

        try:
            if command == "run_program":
                program = params.get("program", {})
                cycles = program.get("cycles", 30)
                steps = program.get("steps", [
                    {"temp_C": 95, "duration_s": 30, "name": "denature"},
                    {"temp_C": 60, "duration_s": 30, "name": "anneal"},
                    {"temp_C": 72, "duration_s": 60, "name": "extend"},
                ])

                self._running_program = program.get("name", "PCR")
                self._status = EquipmentStatus.BUSY

                # Simulate quick run
                await asyncio.sleep(0.2)

                self._running_program = None
                self._status = EquipmentStatus.AVAILABLE
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "program": program.get("name", "PCR"),
                    "cycles_completed": cycles,
                    "total_steps": len(steps) * cycles,
                    "final_temp_C": 4.0,
                }

            elif command == "set_temperature":
                target = params.get("temperature_C", 25.0)
                await asyncio.sleep(0.1)
                self._block_temperature = target
                result.status = CommandStatus.COMPLETED
                result.data = {"block_temperature_C": target}

            elif command == "set_lid_temperature":
                target = params.get("temperature_C", 105.0)
                await asyncio.sleep(0.1)
                self._lid_temperature = target
                result.status = CommandStatus.COMPLETED
                result.data = {"lid_temperature_C": target}

            elif command == "open_lid":
                await asyncio.sleep(0.1)
                self._lid_open = True
                result.status = CommandStatus.COMPLETED
                result.data = {"lid_open": True}

            elif command == "close_lid":
                await asyncio.sleep(0.1)
                self._lid_open = False
                result.status = CommandStatus.COMPLETED
                result.data = {"lid_open": False}

            elif command in ("home", "reset"):
                await asyncio.sleep(0.2)
                self._block_temperature = 25.0
                self._lid_temperature = 25.0
                self._lid_open = True
                self._running_program = None
                result.status = CommandStatus.COMPLETED

            elif command in ("pause", "resume", "abort"):
                await asyncio.sleep(0.05)
                result.status = CommandStatus.COMPLETED
                result.data = {"action": command}

        except Exception as e:
            result.status = CommandStatus.FAILED
            result.error = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = (
            result.completed_at - result.started_at
        ).total_seconds() * 1000
        self._record_command(result)
        return result

    async def get_status(self) -> Dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "name": self.name,
            "connected": self._connected,
            "status": self._status.value,
            "block_temperature_C": self._block_temperature,
            "lid_temperature_C": self._lid_temperature,
            "lid_open": self._lid_open,
            "running_program": self._running_program,
        }

    async def calibrate(self, calibration_type: str = "full") -> CalibrationReport:
        logger.info(f"Calibrating {self.name}: {calibration_type}")
        self._status = EquipmentStatus.CALIBRATING
        await asyncio.sleep(0.3)

        report = CalibrationReport(
            instrument_id=self.instrument_id,
            calibration_type=calibration_type,
            passed=True,
            measurements={
                "block_uniformity_C": 0.3,
                "temp_accuracy_C": 0.2,
                "ramp_rate_C_per_s": 2.9,
                "lid_temp_accuracy_C": 0.5,
            },
        )
        self._status = EquipmentStatus.AVAILABLE
        return report


class IncubatorDriver(RobotDriver):
    """
    Driver for laboratory incubators.

    Controls temperature, CO2, humidity, and door operations.
    """

    SUPPORTED_COMMANDS = {
        "set_temperature", "set_co2", "set_humidity",
        "open_door", "close_door", "get_environment",
        "home", "reset",
    }

    def __init__(
        self,
        instrument_id: str,
        name: str = "Incubator",
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            instrument_id, name, EquipmentType.INCUBATOR, connection_config
        )
        self._temperature: float = 37.0
        self._co2_pct: float = 5.0
        self._humidity_pct: float = 95.0
        self._door_open = False
        self._shelves: Dict[int, Optional[str]] = {i: None for i in range(1, 11)}

    async def connect(self) -> bool:
        logger.info(f"Connecting to incubator: {self.name}")
        await asyncio.sleep(0.1)
        self._connected = True
        self._status = EquipmentStatus.AVAILABLE
        self._properties = {
            "temp_range_C": (4, 50),
            "co2_range_pct": (0, 20),
            "humidity_range_pct": (40, 97),
            "shelves": 10,
        }
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        self._status = EquipmentStatus.OFFLINE
        return True

    async def execute_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> CommandResult:
        params = parameters or {}
        if command not in self.SUPPORTED_COMMANDS:
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Unknown command: {command}",
            )
        if not self._connected:
            return CommandResult(
                status=CommandStatus.FAILED,
                error="Not connected",
            )

        start = datetime.utcnow()
        result = CommandResult(started_at=start)

        try:
            if command == "set_temperature":
                target = params.get("temperature_C", 37.0)
                await asyncio.sleep(0.1)
                self._temperature = target
                result.status = CommandStatus.COMPLETED
                result.data = {"temperature_C": target}

            elif command == "set_co2":
                target = params.get("co2_pct", 5.0)
                await asyncio.sleep(0.1)
                self._co2_pct = target
                result.status = CommandStatus.COMPLETED
                result.data = {"co2_pct": target}

            elif command == "set_humidity":
                target = params.get("humidity_pct", 95.0)
                await asyncio.sleep(0.1)
                self._humidity_pct = target
                result.status = CommandStatus.COMPLETED
                result.data = {"humidity_pct": target}

            elif command == "open_door":
                await asyncio.sleep(0.1)
                self._door_open = True
                result.status = CommandStatus.COMPLETED
                result.data = {"door_open": True}

            elif command == "close_door":
                await asyncio.sleep(0.1)
                self._door_open = False
                result.status = CommandStatus.COMPLETED
                result.data = {"door_open": False}

            elif command == "get_environment":
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "temperature_C": self._temperature,
                    "co2_pct": self._co2_pct,
                    "humidity_pct": self._humidity_pct,
                    "door_open": self._door_open,
                    "shelves_occupied": sum(
                        1 for v in self._shelves.values() if v is not None
                    ),
                }

            elif command in ("home", "reset"):
                await asyncio.sleep(0.2)
                self._temperature = 37.0
                self._co2_pct = 5.0
                self._humidity_pct = 95.0
                result.status = CommandStatus.COMPLETED

        except Exception as e:
            result.status = CommandStatus.FAILED
            result.error = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = (
            result.completed_at - result.started_at
        ).total_seconds() * 1000
        self._record_command(result)
        return result

    async def get_status(self) -> Dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "name": self.name,
            "connected": self._connected,
            "status": self._status.value,
            "temperature_C": self._temperature,
            "co2_pct": self._co2_pct,
            "humidity_pct": self._humidity_pct,
            "door_open": self._door_open,
            "shelves_occupied": sum(
                1 for v in self._shelves.values() if v is not None
            ),
        }

    async def calibrate(self, calibration_type: str = "full") -> CalibrationReport:
        logger.info(f"Calibrating {self.name}: {calibration_type}")
        self._status = EquipmentStatus.CALIBRATING
        await asyncio.sleep(0.3)

        report = CalibrationReport(
            instrument_id=self.instrument_id,
            calibration_type=calibration_type,
            passed=True,
            measurements={
                "temp_accuracy_C": 0.2,
                "temp_uniformity_C": 0.5,
                "co2_accuracy_pct": 0.1,
                "humidity_accuracy_pct": 2.0,
            },
        )
        self._status = EquipmentStatus.AVAILABLE
        return report


class RoboticArmDriver(RobotDriver):
    """
    Driver for robotic arms / plate movers.

    Handles plate transport between instruments on the automation deck.
    """

    SUPPORTED_COMMANDS = {
        "pick_plate", "place_plate", "move_to", "grip", "release",
        "home", "reset", "transport",
    }

    def __init__(
        self,
        instrument_id: str,
        name: str = "Robotic Arm",
        connection_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            instrument_id, name, EquipmentType.ROBOTIC_ARM, connection_config
        )
        self._holding_plate: Optional[str] = None
        self._position = {"joint1": 0.0, "joint2": 0.0, "joint3": 0.0}

    async def connect(self) -> bool:
        logger.info(f"Connecting to robotic arm: {self.name}")
        await asyncio.sleep(0.1)
        self._connected = True
        self._status = EquipmentStatus.AVAILABLE
        self._properties = {
            "reach_mm": 850,
            "payload_kg": 2.0,
            "repeatability_mm": 0.02,
            "axes": 6,
        }
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        self._status = EquipmentStatus.OFFLINE
        return True

    async def execute_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> CommandResult:
        params = parameters or {}
        if command not in self.SUPPORTED_COMMANDS:
            return CommandResult(
                status=CommandStatus.FAILED,
                error=f"Unknown command: {command}",
            )
        if not self._connected:
            return CommandResult(
                status=CommandStatus.FAILED,
                error="Not connected",
            )

        start = datetime.utcnow()
        result = CommandResult(started_at=start)

        try:
            if command == "pick_plate":
                location = params.get("location", "nest_1")
                plate_id = params.get("plate_id", "unknown")
                await asyncio.sleep(0.1)
                self._holding_plate = plate_id
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "plate_id": plate_id,
                    "picked_from": location,
                }

            elif command == "place_plate":
                location = params.get("location", "nest_1")
                await asyncio.sleep(0.1)
                placed = self._holding_plate
                self._holding_plate = None
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "plate_id": placed,
                    "placed_at": location,
                }

            elif command == "transport":
                source = params.get("source", "nest_1")
                destination = params.get("destination", "nest_2")
                plate_id = params.get("plate_id", "unknown")
                await asyncio.sleep(0.15)
                result.status = CommandStatus.COMPLETED
                result.data = {
                    "plate_id": plate_id,
                    "source": source,
                    "destination": destination,
                }

            elif command == "move_to":
                position = params.get("position", {})
                await asyncio.sleep(0.08)
                self._position.update(position)
                result.status = CommandStatus.COMPLETED
                result.data = {"position": self._position}

            elif command == "grip":
                force_n = params.get("force_N", 5.0)
                await asyncio.sleep(0.05)
                result.status = CommandStatus.COMPLETED
                result.data = {"grip_force_N": force_n}

            elif command == "release":
                await asyncio.sleep(0.03)
                result.status = CommandStatus.COMPLETED

            elif command in ("home", "reset"):
                await asyncio.sleep(0.2)
                self._holding_plate = None
                self._position = {"joint1": 0.0, "joint2": 0.0, "joint3": 0.0}
                result.status = CommandStatus.COMPLETED

        except Exception as e:
            result.status = CommandStatus.FAILED
            result.error = str(e)

        result.completed_at = datetime.utcnow()
        result.duration_ms = (
            result.completed_at - result.started_at
        ).total_seconds() * 1000
        self._record_command(result)
        return result

    async def get_status(self) -> Dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "name": self.name,
            "connected": self._connected,
            "status": self._status.value,
            "holding_plate": self._holding_plate,
            "position": self._position,
        }

    async def calibrate(self, calibration_type: str = "full") -> CalibrationReport:
        logger.info(f"Calibrating {self.name}: {calibration_type}")
        self._status = EquipmentStatus.CALIBRATING
        await asyncio.sleep(0.3)

        import random
        rng = random.Random(42)

        report = CalibrationReport(
            instrument_id=self.instrument_id,
            calibration_type=calibration_type,
            passed=True,
            measurements={
                "repeatability_mm": 0.02 + rng.gauss(0, 0.005),
                "position_accuracy_mm": 0.1 + rng.gauss(0, 0.02),
                "grip_force_accuracy_N": 0.3,
            },
        )
        self._status = EquipmentStatus.AVAILABLE
        return report


class DriverRegistry:
    """
    Central registry for managing all connected instrument drivers.

    Provides lookup by ID, type, and status, plus lifecycle management.
    """

    def __init__(self) -> None:
        self._drivers: Dict[str, RobotDriver] = {}
        self._driver_types: Dict[str, Type[RobotDriver]] = {
            "liquid_handler": LiquidHandlerDriver,
            "plate_reader": PlateReaderDriver,
            "thermocycler": ThermocyclerDriver,
            "incubator": IncubatorDriver,
            "robotic_arm": RoboticArmDriver,
        }
        logger.info("DriverRegistry initialized")

    def register(self, driver: RobotDriver) -> None:
        """Register a driver instance."""
        self._drivers[driver.instrument_id] = driver
        logger.info(
            f"Registered driver: {driver.name} ({driver.instrument_id}) "
            f"type={driver.equipment_type.value}"
        )

    def unregister(self, instrument_id: str) -> Optional[RobotDriver]:
        """Unregister and return a driver."""
        return self._drivers.pop(instrument_id, None)

    def get(self, instrument_id: str) -> Optional[RobotDriver]:
        """Get a driver by instrument ID."""
        return self._drivers.get(instrument_id)

    def get_by_type(self, equipment_type: EquipmentType) -> List[RobotDriver]:
        """Get all drivers of a specific equipment type."""
        return [
            d for d in self._drivers.values()
            if d.equipment_type == equipment_type
        ]

    def get_available(
        self,
        equipment_type: Optional[EquipmentType] = None,
    ) -> List[RobotDriver]:
        """Get all available (connected + not busy) drivers."""
        drivers = self._drivers.values()
        if equipment_type:
            drivers = [d for d in drivers if d.equipment_type == equipment_type]
        return [
            d for d in drivers
            if d.connected and d.status == EquipmentStatus.AVAILABLE
        ]

    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all registered instruments."""
        results: Dict[str, bool] = {}
        for iid, driver in self._drivers.items():
            try:
                results[iid] = await driver.connect()
            except Exception as e:
                logger.error(f"Failed to connect {driver.name}: {e}")
                results[iid] = False
        return results

    async def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect from all instruments."""
        results: Dict[str, bool] = {}
        for iid, driver in self._drivers.items():
            try:
                results[iid] = await driver.disconnect()
            except Exception as e:
                logger.error(f"Failed to disconnect {driver.name}: {e}")
                results[iid] = False
        return results

    async def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered instruments."""
        statuses: Dict[str, Dict[str, Any]] = {}
        for iid, driver in self._drivers.items():
            try:
                statuses[iid] = await driver.get_status()
            except Exception as e:
                statuses[iid] = {"error": str(e)}
        return statuses

    async def calibrate_all(
        self,
        calibration_type: str = "quick",
    ) -> Dict[str, CalibrationReport]:
        """Run calibration on all connected instruments."""
        reports: Dict[str, CalibrationReport] = {}
        for iid, driver in self._drivers.items():
            if driver.connected:
                try:
                    reports[iid] = await driver.calibrate(calibration_type)
                except Exception as e:
                    logger.error(f"Calibration failed for {driver.name}: {e}")
                    reports[iid] = CalibrationReport(
                        instrument_id=iid,
                        calibration_type=calibration_type,
                        passed=False,
                        recommendations=[f"Calibration error: {e}"],
                    )
        return reports

    @property
    def all_drivers(self) -> Dict[str, RobotDriver]:
        """Get all registered drivers."""
        return dict(self._drivers)

    @property
    def connected_count(self) -> int:
        """Count of connected instruments."""
        return sum(1 for d in self._drivers.values() if d.connected)

    @property
    def total_count(self) -> int:
        """Total registered instruments."""
        return len(self._drivers)
