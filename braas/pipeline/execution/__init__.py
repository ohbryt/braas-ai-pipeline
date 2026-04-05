"""
BRaaS Pipeline Stage 5 - Robotic Execution.

Provides robot orchestration, instrument drivers, vision-based QC,
and autonomous error recovery for automated experiment execution.
"""
from braas.pipeline.execution.orchestrator import (
    RobotOrchestrator,
    RobotTask,
    ExecutionPlan,
)
from braas.pipeline.execution.robot_drivers import (
    RobotDriver,
    LiquidHandlerDriver,
    PlateReaderDriver,
    ThermocyclerDriver,
    IncubatorDriver,
    RoboticArmDriver,
    DriverRegistry,
)
from braas.pipeline.execution.vision_qc import VisionQualityControl
from braas.pipeline.execution.error_recovery import ErrorRecoveryAgent

__all__ = [
    "RobotOrchestrator",
    "RobotTask",
    "ExecutionPlan",
    "RobotDriver",
    "LiquidHandlerDriver",
    "PlateReaderDriver",
    "ThermocyclerDriver",
    "IncubatorDriver",
    "RoboticArmDriver",
    "DriverRegistry",
    "VisionQualityControl",
    "ErrorRecoveryAgent",
]
