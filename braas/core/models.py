"""
BRaaS Core Data Models
=======================

Pydantic v2 data models representing all domain entities in the BRaaS
pipeline: experiments, protocols, samples, equipment, scheduling,
results, anomalies, reports, users, and lab status.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


def _utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def _uuid_hex() -> str:
    """Generate a new UUID hex string."""
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Protocol & Steps
# ---------------------------------------------------------------------------


class ProtocolStep(BaseModel):
    """A single step within an experimental protocol.

    Represents one discrete action such as pipetting, incubation,
    centrifugation, or measurement.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    step_index: int = Field(..., ge=0, description="Zero-based step order index")
    name: str = Field(..., min_length=1, max_length=200, description="Step name")
    description: str = Field(default="", max_length=2000, description="Detailed instructions")
    duration_seconds: float = Field(..., gt=0, description="Expected duration in seconds")
    temperature_celsius: float | None = Field(
        default=None, ge=-200, le=200, description="Required temperature in Celsius"
    )
    equipment_type: EquipmentType | None = Field(
        default=None, description="Equipment required for this step"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Step-specific key-value parameters"
    )
    is_critical: bool = Field(
        default=False, description="Whether failure here aborts the experiment"
    )
    checkpoint: bool = Field(
        default=False, description="Whether to pause for validation after this step"
    )


class Protocol(BaseModel):
    """Complete experimental protocol with ordered steps.

    A protocol defines the full set of instructions to carry out
    a specific experiment type, including required reagents,
    equipment, and safety constraints.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    protocol_id: str = Field(default_factory=_uuid_hex, description="Unique protocol identifier")
    name: str = Field(..., min_length=1, max_length=300, description="Protocol name")
    version: str = Field(default="1.0.0", description="Semantic version string")
    experiment_type: ExperimentType = Field(..., description="Type of experiment")
    safety_level: SafetyLevel = Field(
        default=SafetyLevel.BSL1, description="Required biosafety level"
    )
    steps: list[ProtocolStep] = Field(
        default_factory=list, min_length=1, description="Ordered protocol steps"
    )
    required_equipment: list[EquipmentType] = Field(
        default_factory=list, description="All equipment types needed"
    )
    estimated_duration_seconds: float = Field(
        default=0, ge=0, description="Total estimated duration"
    )
    author: str = Field(default="", description="Protocol author")
    notes: str = Field(default="", max_length=5000, description="Additional notes")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @model_validator(mode="after")
    def _compute_duration(self) -> Protocol:
        """Auto-compute estimated duration from step durations if not set."""
        if self.estimated_duration_seconds == 0 and self.steps:
            self.estimated_duration_seconds = sum(s.duration_seconds for s in self.steps)
        return self

    @field_validator("steps")
    @classmethod
    def _validate_step_order(cls, steps: list[ProtocolStep]) -> list[ProtocolStep]:
        """Ensure steps have sequential indices starting from 0."""
        for i, step in enumerate(steps):
            if step.step_index != i:
                raise ValueError(
                    f"Step at position {i} has step_index={step.step_index}, expected {i}"
                )
        return steps


# ---------------------------------------------------------------------------
# Samples & Reagents
# ---------------------------------------------------------------------------


class Sample(BaseModel):
    """A biological sample used in or produced by an experiment."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    sample_id: str = Field(default_factory=_uuid_hex, description="Unique sample identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Sample name/label")
    sample_type: SampleType = Field(..., description="Biological sample type")
    source: str = Field(default="", description="Origin of the sample")
    concentration: float | None = Field(
        default=None, ge=0, description="Concentration in ng/µL or cells/mL"
    )
    concentration_unit: str = Field(default="ng/uL", description="Unit for concentration")
    volume_ul: float | None = Field(default=None, ge=0, description="Volume in microliters")
    storage_temperature_celsius: float = Field(
        default=-20.0, description="Storage temperature"
    )
    barcode: str = Field(default="", description="Physical barcode ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=_utcnow)
    expiry_date: datetime | None = Field(default=None, description="Sample expiration")

    @property
    def is_expired(self) -> bool:
        """Check if the sample is past its expiry date."""
        if self.expiry_date is None:
            return False
        return datetime.now(timezone.utc) > self.expiry_date


class Reagent(BaseModel):
    """A chemical reagent or biological kit component."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    reagent_id: str = Field(default_factory=_uuid_hex, description="Unique reagent identifier")
    name: str = Field(..., min_length=1, max_length=300, description="Reagent name")
    reagent_type: ReagentType = Field(..., description="Reagent category")
    catalog_number: str = Field(default="", description="Manufacturer catalog number")
    manufacturer: str = Field(default="", description="Manufacturer name")
    lot_number: str = Field(default="", description="Lot/batch number")
    concentration: float | None = Field(default=None, ge=0, description="Stock concentration")
    concentration_unit: str = Field(default="", description="Unit for concentration")
    volume_remaining_ul: float = Field(default=0, ge=0, description="Remaining volume (µL)")
    storage_temperature_celsius: float = Field(default=4.0, description="Storage temperature")
    safety_level: SafetyLevel = Field(default=SafetyLevel.BSL1, description="Safety classification")
    cost_per_unit: float = Field(default=0.0, ge=0, description="Cost per unit in USD")
    expiry_date: datetime | None = Field(default=None, description="Reagent expiration")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return datetime.now(timezone.utc) > self.expiry_date


# ---------------------------------------------------------------------------
# Equipment & Scheduling
# ---------------------------------------------------------------------------


class Equipment(BaseModel):
    """A piece of laboratory equipment/instrument."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    equipment_id: str = Field(default_factory=_uuid_hex, description="Unique equipment identifier")
    name: str = Field(..., min_length=1, max_length=300, description="Equipment name")
    equipment_type: EquipmentType = Field(..., description="Equipment category")
    model_number: str = Field(default="", description="Model/serial number")
    location: str = Field(default="", description="Physical location in the lab")
    is_available: bool = Field(default=True, description="Whether currently available")
    is_operational: bool = Field(default=True, description="Whether in working order")
    safety_level: SafetyLevel = Field(
        default=SafetyLevel.BSL1, description="Required BSL for operation"
    )
    capabilities: list[str] = Field(
        default_factory=list, description="Specific capabilities/features"
    )
    last_calibration: datetime | None = Field(default=None, description="Last calibration date")
    next_maintenance: datetime | None = Field(default=None, description="Next scheduled maintenance")
    utilization_percent: float = Field(
        default=0.0, ge=0, le=100, description="Current utilization percentage"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def needs_calibration(self) -> bool:
        """Check if calibration is overdue (>90 days since last)."""
        if self.last_calibration is None:
            return True
        from datetime import timedelta

        return (datetime.now(timezone.utc) - self.last_calibration) > timedelta(days=90)


class ScheduleSlot(BaseModel):
    """A reserved time slot for equipment or lab usage."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    slot_id: str = Field(default_factory=_uuid_hex, description="Unique slot identifier")
    experiment_id: str = Field(..., description="Associated experiment ID")
    equipment_id: str = Field(..., description="Reserved equipment ID")
    start_time: datetime = Field(..., description="Slot start time (UTC)")
    end_time: datetime = Field(..., description="Slot end time (UTC)")
    priority: Priority = Field(default=Priority.MEDIUM, description="Scheduling priority")
    is_confirmed: bool = Field(default=False, description="Whether the slot is confirmed")
    notes: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def _validate_time_range(self) -> ScheduleSlot:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self

    @property
    def duration_seconds(self) -> float:
        """Duration of the slot in seconds."""
        return (self.end_time - self.start_time).total_seconds()


# ---------------------------------------------------------------------------
# Experiment (top-level aggregate)
# ---------------------------------------------------------------------------


class Experiment(BaseModel):
    """Top-level experiment entity — the primary aggregate in BRaaS.

    An Experiment links a protocol with samples, reagents, schedule,
    and tracks status through the full pipeline lifecycle.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    experiment_id: str = Field(default_factory=_uuid_hex, description="Unique experiment ID")
    name: str = Field(..., min_length=1, max_length=300, description="Experiment name")
    description: str = Field(default="", max_length=5000, description="Experiment description")
    experiment_type: ExperimentType = Field(..., description="Type of experiment")
    status: ExperimentStatus = Field(
        default=ExperimentStatus.DRAFT, description="Current lifecycle status"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="Scheduling priority")
    safety_level: SafetyLevel = Field(default=SafetyLevel.BSL1, description="Required BSL")
    protocol: Protocol | None = Field(default=None, description="Linked protocol")
    samples: list[Sample] = Field(default_factory=list, description="Input samples")
    reagents: list[Reagent] = Field(default_factory=list, description="Required reagents")
    schedule_slots: list[ScheduleSlot] = Field(
        default_factory=list, description="Reserved equipment slots"
    )
    owner_id: str = Field(default="", description="User ID of the experiment owner")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    started_at: datetime | None = Field(default=None, description="When execution began")
    completed_at: datetime | None = Field(default=None, description="When execution finished")
    correlation_id: str = Field(
        default_factory=_uuid_hex, description="Tracing correlation ID"
    )

    @property
    def duration_seconds(self) -> float | None:
        """Actual experiment duration, if started and completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


# ---------------------------------------------------------------------------
# Results & Analysis
# ---------------------------------------------------------------------------


class ExperimentResult(BaseModel):
    """Results produced by experiment analysis.

    Holds raw data references, computed metrics, statistical summaries,
    and quality scores.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    result_id: str = Field(default_factory=_uuid_hex, description="Unique result identifier")
    experiment_id: str = Field(..., description="Parent experiment ID")
    raw_data_uri: str = Field(default="", description="URI to raw data file(s)")
    processed_data_uri: str = Field(default="", description="URI to processed data")
    summary: dict[str, Any] = Field(default_factory=dict, description="Key result metrics")
    quality_score: float = Field(
        default=0.0, ge=0, le=1.0, description="Overall quality score (0-1)"
    )
    statistical_tests: list[dict[str, Any]] = Field(
        default_factory=list, description="Statistical test results"
    )
    plots_uris: list[str] = Field(default_factory=list, description="URIs to generated plots")
    ml_predictions: dict[str, Any] = Field(
        default_factory=dict, description="ML model prediction outputs"
    )
    notes: str = Field(default="", max_length=5000)
    created_at: datetime = Field(default_factory=_utcnow)

    @property
    def passed_qc(self) -> bool:
        """Whether the result passes quality control (score >= 0.7)."""
        return self.quality_score >= 0.7


class AnomalyEvent(BaseModel):
    """An anomaly detected during experiment execution or monitoring.

    Captures sensor deviations, unexpected readings, equipment faults,
    and other irregularities that the monitoring system flags.
    """

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    anomaly_id: str = Field(default_factory=_uuid_hex, description="Unique anomaly identifier")
    experiment_id: str = Field(..., description="Associated experiment ID")
    level: AnomalyLevel = Field(..., description="Severity level")
    category: str = Field(default="", description="Anomaly category (e.g. 'temperature', 'pressure')")
    message: str = Field(..., min_length=1, max_length=2000, description="Description of the anomaly")
    detected_at: datetime = Field(default_factory=_utcnow, description="Detection timestamp")
    source: str = Field(default="", description="Detection source (sensor, model, manual)")
    metric_name: str = Field(default="", description="Name of the metric that triggered")
    expected_value: float | None = Field(default=None, description="Expected normal value")
    actual_value: float | None = Field(default=None, description="Observed anomalous value")
    acknowledged: bool = Field(default=False, description="Whether reviewed by a human")
    resolution: str = Field(default="", description="How the anomaly was resolved")
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Reports & Users
# ---------------------------------------------------------------------------


class Report(BaseModel):
    """A generated report summarizing experiment outcomes."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    report_id: str = Field(default_factory=_uuid_hex, description="Unique report identifier")
    experiment_id: str = Field(..., description="Associated experiment ID")
    title: str = Field(..., min_length=1, max_length=500, description="Report title")
    format: str = Field(default="pdf", description="Output format (pdf, html, json)")
    sections: list[dict[str, Any]] = Field(
        default_factory=list, description="Report section contents"
    )
    file_uri: str = Field(default="", description="URI to the generated report file")
    generated_at: datetime = Field(default_factory=_utcnow)
    generated_by: str = Field(default="system", description="Generator identity")
    version: str = Field(default="1.0", description="Report version")
    metadata: dict[str, Any] = Field(default_factory=dict)


class User(BaseModel):
    """A BRaaS platform user (researcher, technician, admin)."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    user_id: str = Field(default_factory=_uuid_hex, description="Unique user identifier")
    username: str = Field(..., min_length=1, max_length=100, description="Login username")
    email: str = Field(..., description="Email address")
    full_name: str = Field(default="", max_length=200, description="Full display name")
    role: str = Field(default="researcher", description="User role")
    lab_id: str = Field(default="", description="Associated lab identifier")
    safety_certifications: list[SafetyLevel] = Field(
        default_factory=list, description="BSL certifications held"
    )
    is_active: bool = Field(default=True, description="Account active status")
    created_at: datetime = Field(default_factory=_utcnow)
    last_login: datetime | None = Field(default=None, description="Last login timestamp")
    preferences: dict[str, Any] = Field(default_factory=dict)

    def is_certified_for(self, level: SafetyLevel) -> bool:
        """Check if user holds certification for the given BSL."""
        return level in self.safety_certifications


# ---------------------------------------------------------------------------
# Lab Status (aggregate dashboard model)
# ---------------------------------------------------------------------------


class LabStatus(BaseModel):
    """Real-time lab status snapshot for dashboards and monitoring."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    lab_id: str = Field(..., description="Lab identifier")
    lab_name: str = Field(default="", description="Human-readable lab name")
    active_experiments: int = Field(default=0, ge=0, description="Currently running experiments")
    queued_experiments: int = Field(default=0, ge=0, description="Experiments waiting to run")
    total_equipment: int = Field(default=0, ge=0, description="Total equipment pieces")
    available_equipment: int = Field(default=0, ge=0, description="Currently available equipment")
    active_anomalies: int = Field(default=0, ge=0, description="Unresolved anomaly count")
    safety_level: SafetyLevel = Field(
        default=SafetyLevel.BSL1, description="Lab's maximum BSL rating"
    )
    occupancy_percent: float = Field(
        default=0.0, ge=0, le=100, description="Current lab occupancy"
    )
    temperature_celsius: float | None = Field(
        default=None, description="Ambient temperature reading"
    )
    humidity_percent: float | None = Field(
        default=None, ge=0, le=100, description="Ambient humidity reading"
    )
    last_updated: datetime = Field(default_factory=_utcnow)
    alerts: list[str] = Field(default_factory=list, description="Active alert messages")

    @property
    def equipment_utilization_percent(self) -> float:
        """Percentage of equipment currently in use."""
        if self.total_equipment == 0:
            return 0.0
        in_use = self.total_equipment - self.available_equipment
        return round((in_use / self.total_equipment) * 100, 1)
