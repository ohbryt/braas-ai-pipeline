"""
BRaaS Custom Exceptions
========================

Hierarchical exception classes for precise error handling across
the BRaaS pipeline. All exceptions inherit from BRaaSError to allow
broad or granular catching patterns.
"""

from __future__ import annotations

from typing import Any


class BRaaSError(Exception):
    """Base exception for all BRaaS pipeline errors.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code for API responses.
        details: Additional structured context about the error.
        experiment_id: Associated experiment ID, if applicable.
    """

    def __init__(
        self,
        message: str,
        code: str = "BRAAS_ERROR",
        details: dict[str, Any] | None = None,
        experiment_id: str | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        self.experiment_id = experiment_id
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize exception for API error responses."""
        result: dict[str, Any] = {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }
        if self.experiment_id:
            result["experiment_id"] = self.experiment_id
        return result

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code!r}, "
            f"experiment_id={self.experiment_id!r})"
        )


class ValidationError(BRaaSError):
    """Raised when experiment input validation fails.

    Examples: invalid reagent concentrations, incompatible sample types,
    missing required protocol steps, out-of-range parameters.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        constraint: str | None = None,
        details: dict[str, Any] | None = None,
        experiment_id: str | None = None,
    ) -> None:
        _details = details or {}
        if field:
            _details["field"] = field
        if constraint:
            _details["constraint"] = constraint
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=_details,
            experiment_id=experiment_id,
        )
        self.field = field
        self.constraint = constraint


class SafetyError(BRaaSError):
    """Raised when a safety constraint is violated.

    Examples: BSL level mismatch, missing PPE verification,
    hazardous reagent combination, unauthorized access.
    """

    def __init__(
        self,
        message: str,
        safety_level: str | None = None,
        violation_type: str | None = None,
        details: dict[str, Any] | None = None,
        experiment_id: str | None = None,
    ) -> None:
        _details = details or {}
        if safety_level:
            _details["safety_level"] = safety_level
        if violation_type:
            _details["violation_type"] = violation_type
        super().__init__(
            message=message,
            code="SAFETY_ERROR",
            details=_details,
            experiment_id=experiment_id,
        )
        self.safety_level = safety_level
        self.violation_type = violation_type


class SchedulingError(BRaaSError):
    """Raised when experiment scheduling fails.

    Examples: equipment conflict, no available time slots,
    resource unavailable, dependency not met.
    """

    def __init__(
        self,
        message: str,
        resource: str | None = None,
        requested_slot: str | None = None,
        details: dict[str, Any] | None = None,
        experiment_id: str | None = None,
    ) -> None:
        _details = details or {}
        if resource:
            _details["resource"] = resource
        if requested_slot:
            _details["requested_slot"] = requested_slot
        super().__init__(
            message=message,
            code="SCHEDULING_ERROR",
            details=_details,
            experiment_id=experiment_id,
        )
        self.resource = resource
        self.requested_slot = requested_slot


class ExecutionError(BRaaSError):
    """Raised during experiment execution failures.

    Examples: protocol step failure, unexpected sensor readings,
    hardware communication timeout, process abort.
    """

    def __init__(
        self,
        message: str,
        step_index: int | None = None,
        step_name: str | None = None,
        recoverable: bool = False,
        details: dict[str, Any] | None = None,
        experiment_id: str | None = None,
    ) -> None:
        _details = details or {}
        if step_index is not None:
            _details["step_index"] = step_index
        if step_name:
            _details["step_name"] = step_name
        _details["recoverable"] = recoverable
        super().__init__(
            message=message,
            code="EXECUTION_ERROR",
            details=_details,
            experiment_id=experiment_id,
        )
        self.step_index = step_index
        self.step_name = step_name
        self.recoverable = recoverable


class AnalysisError(BRaaSError):
    """Raised when data analysis or ML inference fails.

    Examples: model loading failure, invalid data format,
    statistical test failure, insufficient data points.
    """

    def __init__(
        self,
        message: str,
        model_name: str | None = None,
        analysis_type: str | None = None,
        details: dict[str, Any] | None = None,
        experiment_id: str | None = None,
    ) -> None:
        _details = details or {}
        if model_name:
            _details["model_name"] = model_name
        if analysis_type:
            _details["analysis_type"] = analysis_type
        super().__init__(
            message=message,
            code="ANALYSIS_ERROR",
            details=_details,
            experiment_id=experiment_id,
        )
        self.model_name = model_name
        self.analysis_type = analysis_type


class RobotError(BRaaSError):
    """Raised when robotic/automation hardware encounters issues.

    Examples: liquid handler calibration failure, arm collision detected,
    tip pickup failure, communication lost with robot controller.
    """

    def __init__(
        self,
        message: str,
        robot_id: str | None = None,
        command: str | None = None,
        recoverable: bool = False,
        details: dict[str, Any] | None = None,
        experiment_id: str | None = None,
    ) -> None:
        _details = details or {}
        if robot_id:
            _details["robot_id"] = robot_id
        if command:
            _details["command"] = command
        _details["recoverable"] = recoverable
        super().__init__(
            message=message,
            code="ROBOT_ERROR",
            details=_details,
            experiment_id=experiment_id,
        )
        self.robot_id = robot_id
        self.command = command
        self.recoverable = recoverable
