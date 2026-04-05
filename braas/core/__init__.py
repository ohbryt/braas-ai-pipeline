"""
BRaaS Core Module
==================

Core domain objects: data models, enumerations, events, and exceptions.
"""

from braas.core.enums import (
    AnomalyLevel,
    EquipmentType,
    ExperimentStatus,
    ExperimentType,
    Priority,
    ReagentType,
    SafetyLevel,
    SampleType,
)
from braas.core.events import Event, EventBus, get_event_bus, reset_event_bus
from braas.core.exceptions import (
    AnalysisError,
    BRaaSError,
    ExecutionError,
    RobotError,
    SafetyError,
    SchedulingError,
    ValidationError,
)
from braas.core.models import (
    AnomalyEvent,
    Equipment,
    Experiment,
    ExperimentResult,
    LabStatus,
    Protocol,
    ProtocolStep,
    Reagent,
    Report,
    Sample,
    ScheduleSlot,
    User,
)

__all__ = [
    # Enums
    "AnomalyLevel",
    "EquipmentType",
    "ExperimentStatus",
    "ExperimentType",
    "Priority",
    "ReagentType",
    "SafetyLevel",
    "SampleType",
    # Events
    "Event",
    "EventBus",
    "get_event_bus",
    "reset_event_bus",
    # Exceptions
    "AnalysisError",
    "BRaaSError",
    "ExecutionError",
    "RobotError",
    "SafetyError",
    "SchedulingError",
    "ValidationError",
    # Models
    "AnomalyEvent",
    "Equipment",
    "Experiment",
    "ExperimentResult",
    "LabStatus",
    "Protocol",
    "ProtocolStep",
    "Reagent",
    "Report",
    "Sample",
    "ScheduleSlot",
    "User",
]
