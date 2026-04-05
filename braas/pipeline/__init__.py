"""
Pipeline Orchestrator for BRaaS AI Pipeline
============================================

Orchestrates all 10 pipeline stages:
1. Intake - Experiment intake and request parsing
2. Protocol Design - Protocol generation and optimization
3. Validation - Feasibility and safety checks
4. Scheduling - Resource scheduling
5. Execution - Robot execution
6. Monitoring - Real-time monitoring
7. Analysis - Data analysis
8. Reporting - Report generation
9. Learning - ML model updates
10. Knowledge - Knowledge graph updates
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from braas.core.enums import ExperimentStatus, PipelineStage, ValidationStatus
from braas.core.events import Event, EventBus, get_event_bus
from braas.core.models import Experiment, ExperimentResult
from braas.knowledge.graph import KnowledgeGraph
from braas.models.registry import ModelRegistry
from braas.pipeline.validation.feasibility import FeasibilityChecker, FeasibilityReport
from braas.pipeline.validation.safety import SafetyChecker, SafetyReport
from braas.pipeline.validation.digital_twin import DigitalTwinSimulator, PredictedOutcome


class StageStatus(str, Enum):
    """Status of a pipeline stage."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result from a pipeline stage."""
    stage: PipelineStage
    status: StageStatus
    started_at: datetime
    completed_at: datetime | None = None
    output: Any = None
    error: str | None = None
    duration_sec: float | None = None


@dataclass
class PipelineStatus:
    """Overall pipeline status."""
    stages: dict[str, StageStatus]
    current_stage: str | None
    progress_pct: float
    errors: list[str]


@dataclass
class ExperimentResult:
    """Final experiment result with all stage results."""
    experiment_id: str
    experiment: Experiment
    status: ExperimentStatus
    stage_results: dict[PipelineStage, StageResult]
    final_output: Any
    started_at: datetime
    completed_at: datetime | None = None
    digital_twin_prediction: PredictedOutcome | None = None
    feasibility_report: FeasibilityReport | None = None
    safety_report: SafetyReport | None = None


# Stage handler type
StageHandler = Callable[[Experiment, EventBus], Any]


class PipelineOrchestrator:
    """Orchestrates experiment execution across all pipeline stages.
    
    Manages the complete lifecycle of an experiment through
    intake, design, validation, execution, and analysis.
    """
    
    STAGE_ORDER = [
        PipelineStage.INTAKE,
        PipelineStage.PROTOCOL_DESIGN,
        PipelineStage.VALIDATION,
        PipelineStage.SCHEDULING,
        PipelineStage.EXECUTION,
        PipelineStage.MONITORING,
        PipelineStage.ANALYSIS,
        PipelineStage.REPORTING,
        PipelineStage.LEARNING,
        PipelineStage.KNOWLEDGE,
    ]
    
    def __init__(self):
        """Initialize pipeline orchestrator with all stage handlers."""
        self._event_bus = get_event_bus()
        self._model_registry = ModelRegistry()
        self._knowledge_graph = KnowledgeGraph()
        
        # Initialize checkers
        self._feasibility_checker = FeasibilityChecker()
        self._safety_checker = SafetyChecker()
        self._digital_twin = DigitalTwinSimulator()
        
        # Stage handlers
        self._stage_handlers: dict[PipelineStage, StageHandler] = {
            PipelineStage.INTAKE: self._stage_intake,
            PipelineStage.PROTOCOL_DESIGN: self._stage_protocol_design,
            PipelineStage.VALIDATION: self._stage_validation,
            PipelineStage.SCHEDULING: self._stage_scheduling,
            PipelineStage.EXECUTION: self._stage_execution,
            PipelineStage.MONITORING: self._stage_monitoring,
            PipelineStage.ANALYSIS: self._stage_analysis,
            PipelineStage.REPORTING: self._stage_reporting,
            PipelineStage.LEARNING: self._stage_learning,
            PipelineStage.KNOWLEDGE: self._stage_knowledge,
        }
        
        # Track stage statuses
        self._stage_statuses: dict[PipelineStage, StageStatus] = {
            stage: StageStatus.PENDING for stage in self.STAGE_ORDER
        }
        
        # Current experiment tracking
        self._current_experiment_id: str | None = None
        self._stage_results: dict[PipelineStage, StageResult] = {}
        self._errors: list[str] = []
        
        # Cancellation flag
        self._cancelled = False
    
    async def run_experiment(
        self, experiment_request: dict[str, Any]
    ) -> ExperimentResult:
        """Run complete experiment through all pipeline stages.
        
        Args:
            experiment_request: Dict containing experiment configuration
            
        Returns:
            ExperimentResult with all stage results
        """
        start_time = datetime.now()
        self._cancelled = False
        self._errors = []
        
        # Reset stage statuses
        for stage in self.STAGE_ORDER:
            self._stage_statuses[stage] = StageStatus.PENDING
            self._stage_results[stage] = None
        
        # Create experiment from request
        experiment = self._create_experiment(experiment_request)
        self._current_experiment_id = experiment.experiment_id
        
        # Run pre-flight digital twin prediction
        digital_twin_prediction = self._digital_twin.predict_outcome(experiment)
        
        # Create experiment result object
        result = ExperimentResult(
            experiment_id=experiment.experiment_id,
            experiment=experiment,
            status=ExperimentStatus.IN_PROGRESS,
            stage_results={},
            final_output=None,
            started_at=start_time,
            digital_twin_prediction=digital_twin_prediction,
            feasibility_report=None,
            safety_report=None
        )
        
        # Emit start event
        await self._event_bus.emit(Event(
            type="experiment.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        # Run stages - some can run in parallel
        for stage in self.STAGE_ORDER:
            if self._cancelled:
                result.status = ExperimentStatus.CANCELLED
                break
            
            stage_start = datetime.now()
            self._stage_statuses[stage] = StageStatus.RUNNING
            
            try:
                handler = self._stage_handlers.get(stage)
                if handler:
                    output = await asyncio.create_task(
                        asyncio.to_thread(handler, experiment, self._event_bus)
                    )
                else:
                    output = None
                
                stage_completed = datetime.now()
                stage_duration = (stage_completed - stage_start).total_seconds()
                
                stage_result = StageResult(
                    stage=stage,
                    status=StageStatus.COMPLETED,
                    started_at=stage_start,
                    completed_at=stage_completed,
                    output=output,
                    duration_sec=stage_duration
                )
                
                self._stage_results[stage] = stage_result
                self._stage_statuses[stage] = StageStatus.COMPLETED
                
                # Capture validation reports
                if stage == PipelineStage.VALIDATION:
                    result.feasibility_report = output.get("feasibility") if output else None
                    result.safety_report = output.get("safety") if output else None
                
                # Emit stage completion
                await self._event_bus.emit(Event(
                    type=f"stage.{stage.value}.completed",
                    data={"experiment_id": experiment.experiment_id, "stage": stage.value}
                ))
                
            except Exception as e:
                stage_completed = datetime.now()
                stage_duration = (stage_completed - stage_start).total_seconds()
                
                error_msg = f"Stage {stage.value} failed: {str(e)}"
                self._errors.append(error_msg)
                
                stage_result = StageResult(
                    stage=stage,
                    status=StageStatus.FAILED,
                    started_at=stage_start,
                    completed_at=stage_completed,
                    error=error_msg,
                    duration_sec=stage_duration
                )
                
                self._stage_results[stage] = stage_result
                self._stage_statuses[stage] = StageStatus.FAILED
                result.status = ExperimentStatus.FAILED
                
                await self._event_bus.emit(Event(
                    type=f"stage.{stage.value}.failed",
                    data={"experiment_id": experiment.experiment_id, "error": error_msg}
                ))
                
                # Stop pipeline on critical stage failure
                if stage in [PipelineStage.VALIDATION, PipelineStage.EXECUTION]:
                    break
        
        # Finalize result
        result.completed_at = datetime.now()
        result.stage_results = dict(self._stage_results)
        
        if result.status == ExperimentStatus.IN_PROGRESS:
            result.status = ExperimentStatus.COMPLETED
            result.final_output = self._stage_results.get(PipelineStage.ANALYSIS, {}).output
        
        # Emit completion event
        await self._event_bus.emit(Event(
            type="experiment.completed",
            data={
                "experiment_id": experiment.experiment_id,
                "status": result.status.value
            }
        ))
        
        return result
    
    def run_stage(self, stage_name: str, input_data: Any) -> Any:
        """Run a single pipeline stage manually.
        
        Args:
            stage_name: Name of stage to run
            input_data: Input to the stage
            
        Returns:
            Stage output
        """
        try:
            stage = PipelineStage(stage_name)
        except ValueError:
            return {"error": f"Unknown stage: {stage_name}"}
        
        handler = self._stage_handlers.get(stage)
        if not handler:
            return {"error": f"No handler for stage: {stage_name}"}
        
        # Run synchronously
        experiment = input_data if isinstance(input_data, Experiment) else None
        if experiment:
            return asyncio.run(handler(experiment, self._event_bus))
        
        return {"error": "Invalid input for stage"}
    
    def get_pipeline_status(self) -> PipelineStatus:
        """Get current pipeline status.
        
        Returns:
            PipelineStatus with all stage statuses
        """
        stages = {stage.value: status for stage, status in self._stage_statuses.items()}
        
        # Calculate progress
        completed = sum(1 for s in self._stage_statuses.values() if s == StageStatus.COMPLETED)
        progress_pct = (completed / len(self.STAGE_ORDER)) * 100
        
        # Current stage
        current = None
        for stage, status in self._stage_statuses.items():
            if status == StageStatus.RUNNING:
                current = stage.value
                break
        
        return PipelineStatus(
            stages=stages,
            current_stage=current,
            progress_pct=round(progress_pct, 1),
            errors=list(self._errors)
        )
    
    def cancel_experiment(self, exp_id: str) -> bool:
        """Cancel a running experiment.
        
        Args:
            exp_id: Experiment ID to cancel
            
        Returns:
            True if cancelled
        """
        if self._current_experiment_id != exp_id:
            return False
        
        self._cancelled = True
        
        # Emit cancellation event
        asyncio.create_task(self._event_bus.emit(Event(
            type="experiment.cancelled",
            data={"experiment_id": exp_id}
        )))
        
        return True
    
    def get_stage_result(self, stage_name: str) -> StageResult | None:
        """Get result from last run of a stage.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            StageResult if stage was run
        """
        try:
            stage = PipelineStage(stage_name)
        except ValueError:
            return None
        
        return self._stage_results.get(stage)
    
    async def _stage_intake(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Intake stage - process experiment request."""
        await event_bus.emit(Event(
            type="stage.intake.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        # Process intake data
        output = {
            "validated": True,
            "samples_processed": len(experiment.samples),
            "reagents_identified": len(experiment.reagents)
        }
        
        return output
    
    async def _stage_protocol_design(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Protocol design stage - generate/retrieve protocol."""
        await event_bus.emit(Event(
            type="stage.protocol_design.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        # Use existing protocol or generate placeholder
        protocol = experiment.protocol
        
        output = {
            "protocol_id": protocol.protocol_id if protocol else None,
            "steps_count": len(protocol.steps) if protocol else 0,
            "estimated_duration": protocol.estimated_duration_seconds if protocol else 0
        }
        
        return output
    
    async def _stage_validation(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Validation stage - feasibility and safety checks."""
        await event_bus.emit(Event(
            type="stage.validation.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        # Run feasibility check
        feasibility_report = self._feasibility_checker.check_all(experiment)
        
        # Run safety check
        safety_report = self._safety_checker.generate_safety_report(experiment)
        
        output = {
            "feasibility": feasibility_report,
            "safety": safety_report
        }
        
        # Fail if validation failed
        if feasibility_report.status == ValidationStatus.FAIL:
            raise ValueError("Feasibility validation failed")
        
        return output
    
    async def _stage_scheduling(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Scheduling stage - schedule resources."""
        await event_bus.emit(Event(
            type="stage.scheduling.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        # Create schedule slots
        output = {
            "scheduled": True,
            "slots_reserved": len(experiment.schedule_slots)
        }
        
        return output
    
    async def _stage_execution(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Execution stage - run on robots."""
        await event_bus.emit(Event(
            type="stage.execution.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        # Simulate execution
        output = {
            "executed": True,
            "steps_completed": len(experiment.protocol.steps) if experiment.protocol else 0
        }
        
        return output
    
    async def _stage_monitoring(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Monitoring stage - monitor execution."""
        await event_bus.emit(Event(
            type="stage.monitoring.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        output = {
            "monitored": True,
            "anomalies_detected": 0
        }
        
        return output
    
    async def _stage_analysis(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Analysis stage - analyze results."""
        await event_bus.emit(Event(
            type="stage.analysis.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        # Run digital twin prediction
        prediction = self._digital_twin.predict_outcome(experiment)
        
        output = {
            "prediction": prediction.raw_data,
            "confidence": prediction.confidence,
            "signal_range": prediction.signal_range
        }
        
        return output
    
    async def _stage_reporting(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Reporting stage - generate reports."""
        await event_bus.emit(Event(
            type="stage.reporting.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        output = {
            "report_generated": True,
            "formats": ["pdf", "json"]
        }
        
        return output
    
    async def _stage_learning(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Learning stage - update ML models."""
        await event_bus.emit(Event(
            type="stage.learning.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        # Use model registry for learning
        output = {
            "models_updated": [],
            "success_probability": self._digital_twin.estimate_success_probability(experiment)
        }
        
        return output
    
    async def _stage_knowledge(self, experiment: Experiment, event_bus: EventBus) -> dict:
        """Knowledge stage - update knowledge graph."""
        await event_bus.emit(Event(
            type="stage.knowledge.started",
            data={"experiment_id": experiment.experiment_id}
        ))
        
        output = {
            "knowledge_updated": True
        }
        
        return output
    
    def _create_experiment(self, request: dict[str, Any]) -> Experiment:
        """Create Experiment from request dict."""
        from braas.core.models import Experiment
        
        return Experiment(
            experiment_id=request.get("experiment_id", ""),
            name=request.get("name", "Untitled Experiment"),
            description=request.get("description", ""),
            experiment_type=request.get("experiment_type"),
            status=ExperimentStatus.DRAFT,
            priority=request.get("priority"),
            safety_level=request.get("safety_level"),
            protocol=request.get("protocol"),
            samples=request.get("samples", []),
            reagents=request.get("reagents", []),
            schedule_slots=request.get("schedule_slots", []),
            owner_id=request.get("owner_id", ""),
            tags=request.get("tags", []),
            metadata=request.get("metadata", {})
        )
