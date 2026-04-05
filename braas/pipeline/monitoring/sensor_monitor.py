"""
Sensor Monitor
==============

Real-time monitoring of environmental sensors, instrument status,
and experiment process tracking with async streaming support.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from braas.core.enums import EquipmentType, ExperimentStatus
from braas.core.exceptions import ExecutionError
from braas.core.models import AnomalyEvent


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------

@dataclass
class EnvironmentalData:
    """Environmental monitoring data."""
    temp_c: float
    humidity_pct: float
    co2_pct: float
    pressure_mbar: float
    particle_class: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class InstrumentStatus:
    """Status of a laboratory instrument."""
    equipment_id: str
    name: str
    status: str  # 'idle', 'running', 'error', 'maintenance'
    temperature_c: float | None = None
    error_message: str | None = None
    last_maintenance: datetime | None = None
    next_maintenance: datetime | None = None


@dataclass
class ProcessStatus:
    """Status of an experiment process."""
    current_step: int
    progress_pct: float
    elapsed_min: float
    remaining_min: float
    step_history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SensorReading:
    """Single sensor reading from streaming."""
    sensor_id: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# Simulated Sensor Hardware
# -----------------------------------------------------------------------------

class SimulatedSensors:
    """Simulated sensor data for testing without hardware."""
    
    # Normal operating ranges
    ENVIRONMENTAL_RANGES = {
        'temp_c': (18.0, 25.0),      # Lab temperature
        'humidity_pct': (30.0, 60.0),
        'co2_pct': (0.04, 0.06),     # Ambient CO2
        'pressure_mbar': (1010.0, 1020.0),
    }
    
    @classmethod
    def get_environmental_readings(cls) -> dict[str, float]:
        """Generate simulated environmental readings."""
        return {
            'temp_c': random.uniform(*cls.ENVIRONMENTAL_RANGES['temp_c']),
            'humidity_pct': random.uniform(*cls.ENVIRONMENTAL_RANGES['humidity_pct']),
            'co2_pct': random.uniform(*cls.ENVIRONMENTAL_RANGES['co2_pct']),
            'pressure_mbar': random.uniform(*cls.ENVIRONMENTAL_RANGES['pressure_mbar']),
            'particle_class': random.choice(['ISO 7', 'ISO 8', 'ISO 9']),
        }
    
    @classmethod
    def get_instrument_status(cls, equipment_id: str, equipment_type: EquipmentType) -> InstrumentStatus:
        """Generate simulated instrument status."""
        statuses = ['idle', 'running', 'idle', 'running']  # Weighted toward idle/running
        status = random.choice(statuses)
        
        return InstrumentStatus(
            equipment_id=equipment_id,
            name=f"{equipment_type.value} Unit",
            status=status,
            temperature_c=37.0 if status == 'running' else 22.0,
            error_message=None if status != 'error' else "Sensor communication timeout",
        )
    
    @classmethod
    def get_sensor_reading(cls, sensor_type: str) -> tuple[float, str]:
        """Generate a single sensor reading."""
        if sensor_type == 'temperature':
            return (random.uniform(18.0, 25.0), '°C')
        elif sensor_type == 'humidity':
            return (random.uniform(30.0, 60.0), '%')
        elif sensor_type == 'co2':
            return (random.uniform(0.04, 0.06), '%')
        elif sensor_type == 'pressure':
            return (random.uniform(1010.0, 1020.0), 'mbar')
        else:
            return (random.uniform(0, 100), 'units')


# -----------------------------------------------------------------------------
# Sensor Monitor
# -----------------------------------------------------------------------------

class SensorMonitor:
    """Monitor environmental conditions, instrument status, and experiment progress.
    
    Provides both synchronous tracking and asynchronous streaming of sensor data.
    Uses simulated sensors when no hardware is available.
    """
    
    def __init__(self, use_simulation: bool = True) -> None:
        """Initialize the sensor monitor.
        
        Args:
            use_simulation: Use simulated sensors when True, hardware when False
        """
        self._use_simulation = use_simulation
        self._sensor_configs = self._load_sensor_configs()
        self._active_experiments: dict[str, dict[str, Any]] = {}
        self._equipment_registry: dict[str, dict[str, Any]] = {}
    
    def _load_sensor_configs(self) -> dict[str, dict[str, Any]]:
        """Load sensor configuration."""
        # Default sensor configurations
        return {
            'environmental': {
                'sensors': ['temperature', 'humidity', 'co2', 'pressure', 'particles'],
                'update_interval_sec': 60,
            },
            'equipment': {
                'update_interval_sec': 30,
            }
        }
    
    def track_environmental(self) -> EnvironmentalData:
        """Track current environmental conditions.
        
        Returns:
            EnvironmentalData with current readings
        """
        if self._use_simulation:
            readings = SimulatedSensors.get_environmental_readings()
        else:
            # In production, would read from actual sensors
            readings = SimulatedSensors.get_environmental_readings()
        
        return EnvironmentalData(
            temp_c=readings['temp_c'],
            humidity_pct=readings['humidity_pct'],
            co2_pct=readings['co2_pct'],
            pressure_mbar=readings['pressure_mbar'],
            particle_class=readings['particle_class']
        )
    
    def track_instrument_status(self) -> dict[str, InstrumentStatus]:
        """Track status of all registered instruments.
        
        Returns:
            Dictionary mapping equipment_id to InstrumentStatus
        """
        status_map = {}
        
        if not self._equipment_registry:
            # Initialize with some default equipment
            self._equipment_registry = {
                'incubator_01': {'type': EquipmentType.INCUBATOR, 'name': 'CO2 Incubator 1'},
                'centrifuge_01': {'type': EquipmentType.CENTRIFUGE, 'name': 'Microcentrifuge'},
                'pcr_01': {'type': EquipmentType.THERMOCYCLER, 'name': 'qPCR System'},
                'plate_reader_01': {'type': EquipmentType.PLATE_READER, 'name': 'Plate Reader'},
            }
        
        for eq_id, eq_info in self._equipment_registry.items():
            if self._use_simulation:
                status = SimulatedSensors.get_instrument_status(eq_id, eq_info['type'])
            else:
                # Would query actual hardware
                status = SimulatedSensors.get_instrument_status(eq_id, eq_info['type'])
            
            status_map[eq_id] = status
        
        return status_map
    
    def track_process(self, experiment_id: str) -> ProcessStatus:
        """Track the progress of an experiment.
        
        Args:
            experiment_id: ID of the experiment to track
        
        Returns:
            ProcessStatus with current progress
        """
        if experiment_id not in self._active_experiments:
            # Initialize tracking for new experiment
            self._active_experiments[experiment_id] = {
                'start_time': time.time(),
                'total_steps': 10,
                'current_step': 0,
                'step_history': [],
            }
        
        tracking = self._active_experiments[experiment_id]
        elapsed = (time.time() - tracking['start_time']) / 60  # minutes
        current_step = tracking['current_step']
        total_steps = tracking['total_steps']
        
        progress_pct = (current_step / total_steps) * 100 if total_steps > 0 else 0
        remaining_min = (elapsed / progress_pct * 100) * (100 - progress_pct) / 100 if progress_pct > 0 else 0
        
        return ProcessStatus(
            current_step=current_step,
            progress_pct=progress_pct,
            elapsed_min=elapsed,
            remaining_min=remaining_min,
            step_history=tracking['step_history']
        )
    
    def emit_anomaly(
        self,
        anomaly_type: str,
        severity: str,
        details: dict[str, Any]
    ) -> AnomalyEvent:
        """Emit an anomaly event from monitoring.
        
        Args:
            anomaly_type: Type of anomaly (e.g., 'temperature', 'contamination')
            severity: Severity level ('info', 'warning', 'error', 'critical')
            details: Additional details about the anomaly
        
        Returns:
            AnomalyEvent object
        """
        experiment_id = details.get('experiment_id', 'unknown')
        
        event = AnomalyEvent(
            experiment_id=experiment_id,
            level=self._get_anomaly_level(severity),
            category=anomaly_type,
            message=details.get('message', f'{anomaly_type} detected'),
            metric_name=details.get('metric_name', anomaly_type),
            expected_value=details.get('expected_value'),
            actual_value=details.get('actual_value'),
            metadata={
                'severity': severity,
                'sensor_id': details.get('sensor_id'),
                'threshold': details.get('threshold'),
            }
        )
        
        return event
    
    def _get_anomaly_level(self, severity: str) -> str:
        """Map severity string to AnomalyLevel enum."""
        from braas.core.enums import AnomalyLevel
        
        mapping = {
            'info': AnomalyLevel.INFO,
            'warning': AnomalyLevel.WARNING,
            'error': AnomalyLevel.ERROR,
            'critical': AnomalyLevel.CRITICAL,
        }
        return mapping.get(severity.lower(), AnomalyLevel.WARNING)
    
    async def stream_sensors(self, experiment_id: str) -> AsyncGenerator[SensorReading, None]:
        """Stream sensor readings asynchronously.
        
        Args:
            experiment_id: ID of experiment to monitor
        
        Yields:
            SensorReading objects at regular intervals
        """
        sensor_types = ['temperature', 'humidity', 'co2', 'pressure']
        
        while True:
            for sensor_type in sensor_types:
                if self._use_simulation:
                    value, unit = SimulatedSensors.get_sensor_reading(sensor_type)
                else:
                    # Would read from actual sensors
                    value, unit = SimulatedSensors.get_sensor_reading(sensor_type)
                
                yield SensorReading(
                    sensor_id=f"{experiment_id}_{sensor_type}",
                    value=value,
                    unit=unit
                )
            
            # Wait before next reading
            await asyncio.sleep(self._sensor_configs['environmental']['update_interval_sec'])
    
    def register_equipment(
        self,
        equipment_id: str,
        equipment_type: EquipmentType,
        name: str
    ) -> None:
        """Register equipment for monitoring.
        
        Args:
            equipment_id: Unique identifier
            equipment_type: Type of equipment
            name: Human-readable name
        """
        self._equipment_registry[equipment_id] = {
            'type': equipment_type,
            'name': name,
        }
    
    def start_experiment_tracking(
        self,
        experiment_id: str,
        total_steps: int
    ) -> None:
        """Start tracking a new experiment.
        
        Args:
            experiment_id: ID of the experiment
            total_steps: Total number of steps in the protocol
        """
        self._active_experiments[experiment_id] = {
            'start_time': time.time(),
            'total_steps': total_steps,
            'current_step': 0,
            'step_history': [],
        }
    
    def update_step(self, experiment_id: str, step: int) -> None:
        """Update current step for tracked experiment.
        
        Args:
            experiment_id: ID of the experiment
            step: New current step number
        """
        if experiment_id in self._active_experiments:
            tracking = self._active_experiments[experiment_id]
            if step > tracking['current_step']:
                tracking['step_history'].append({
                    'step': tracking['current_step'],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'duration_min': (time.time() - tracking['start_time']) / 60
                })
                tracking['current_step'] = step
    
    def stop_tracking(self, experiment_id: str) -> None:
        """Stop tracking an experiment.
        
        Args:
            experiment_id: ID of the experiment to stop
        """
        if experiment_id in self._active_experiments:
            del self._active_experiments[experiment_id]
