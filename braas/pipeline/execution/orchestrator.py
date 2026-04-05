"""
BRaaS Robot Orchestrator - Coordinate multiple robots and instruments.

Implements a state machine for experiment execution and decomposes
protocols into parallelizable tasks assigned to available robots.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set

from braas.core.enums import (
    EquipmentStatus,
    EquipmentType,
    ExperimentStatus,
    TaskStatus,
)
from braas.core.models import (
    Equipment,
    Experiment,
    Protocol,
    ProtocolStep,
    ScheduleEntry,
)

logger = logging.getLogger(__name__)


class ExecutionState(Enum):
    """State machine states for experiment execution."""
    IDLE = auto()
    PREPARING = auto()
    RUNNING = auto()
    COMPLETING = auto()
    DONE = auto()
    ERROR = auto()
    PAUSED = auto()


# Valid state transitions
VALID_TRANSITIONS: Dict[ExecutionState, Set[ExecutionState]] = {
    ExecutionState.IDLE: {ExecutionState.PREPARING},
    ExecutionState.PREPARING: {ExecutionState.RUNNING, ExecutionState.ERROR},
    ExecutionState.RUNNING: {
        ExecutionState.COMPLETING,
        ExecutionState.PAUSED,
        ExecutionState.ERROR,
    },
    ExecutionState.COMPLETING: {ExecutionState.DONE, ExecutionState.ERROR},
    ExecutionState.PAUSED: {ExecutionState.RUNNING, ExecutionState.ERROR},
    ExecutionState.ERROR: {ExecutionState.PREPARING, ExecutionState.IDLE},
    ExecutionState.DONE: {ExecutionState.IDLE},
}


@dataclass
class RobotTask:
    """
    A single task to be executed by a robot/instrument.

    Represents one atomic unit of work decomposed from a protocol step.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = ""
    step_id: str = ""
    name: str = ""
    description: str = ""
    equipment_type: EquipmentType = EquipmentType.LIQUID_HANDLER
    assigned_equipment_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # task IDs
    estimated_duration: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    actual_duration: Optional[timedelta] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionPlan:
    """
    A plan for executing an experiment's protocol.

    Contains ordered tasks with dependencies, forming a DAG of execution.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_id: str = ""
    protocol_id: str = ""
    tasks: List[RobotTask] = field(default_factory=list)
    state: ExecutionState = ExecutionState.IDLE
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def progress_pct(self) -> float:
        """Calculate execution progress percentage."""
        if not self.tasks:
            return 0.0
        completed = sum(
            1 for t in self.tasks if t.status == TaskStatus.COMPLETED
        )
        return round((completed / len(self.tasks)) * 100, 1)

    @property
    def pending_tasks(self) -> List[RobotTask]:
        """Get tasks that are ready to execute (dependencies met)."""
        completed_ids = {
            t.id for t in self.tasks if t.status == TaskStatus.COMPLETED
        }
        return [
            t for t in self.tasks
            if t.status == TaskStatus.PENDING
            and all(dep in completed_ids for dep in t.dependencies)
        ]

    @property
    def running_tasks(self) -> List[RobotTask]:
        """Get currently running tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.RUNNING]

    @property
    def failed_tasks(self) -> List[RobotTask]:
        """Get failed tasks."""
        return [t for t in self.tasks if t.status == TaskStatus.FAILED]


class RobotOrchestrator:
    """
    Coordinates multiple robots and instruments for experiment execution.

    Manages the lifecycle of experiments through a state machine,
    decomposes protocols into executable tasks, assigns tasks to
    available robots, and monitors execution progress.
    """

    def __init__(self) -> None:
        self._plans: Dict[str, ExecutionPlan] = {}
        self._equipment: Dict[str, Equipment] = {}
        self._equipment_status: Dict[str, EquipmentStatus] = {}
        self._state_callbacks: Dict[ExecutionState, List[Callable]] = {}
        self._task_executor: Optional[Callable] = None
        logger.info("RobotOrchestrator initialized")

    def register_equipment(self, equipment: Equipment) -> None:
        """Register a piece of equipment for task assignment."""
        self._equipment[equipment.id] = equipment
        self._equipment_status[equipment.id] = equipment.status
        logger.info(f"Registered equipment: {equipment.name} ({equipment.id})")

    def set_task_executor(self, executor: Callable) -> None:
        """
        Set the function that executes individual tasks on hardware.

        The executor should accept (RobotTask, Equipment) and return
        a result dict.
        """
        self._task_executor = executor

    def on_state_change(
        self,
        state: ExecutionState,
        callback: Callable,
    ) -> None:
        """Register a callback for state transitions."""
        self._state_callbacks.setdefault(state, []).append(callback)

    async def execute_protocol(
        self,
        experiment: Experiment,
        protocol: Protocol,
        schedule_entries: Optional[List[ScheduleEntry]] = None,
    ) -> ExecutionPlan:
        """
        Execute a protocol for an experiment.

        Full lifecycle:
        1. Decompose protocol into tasks
        2. Create execution plan
        3. Transition through state machine:
           IDLE -> PREPARING -> RUNNING -> COMPLETING -> DONE

        Args:
            experiment: The experiment to execute.
            protocol: The protocol to follow.
            schedule_entries: Optional pre-scheduled time slots.

        Returns:
            The completed ExecutionPlan.
        """
        logger.info(
            f"Starting protocol execution: {protocol.name} "
            f"for experiment {experiment.name}"
        )

        # Create execution plan
        plan = ExecutionPlan(
            experiment_id=experiment.id,
            protocol_id=protocol.id,
        )

        # Decompose protocol into tasks
        tasks = await self.decompose_to_tasks(protocol, experiment.id)
        plan.tasks = tasks
        self._plans[plan.id] = plan

        try:
            # IDLE -> PREPARING
            await self._transition(plan, ExecutionState.PREPARING)
            experiment.status = ExperimentStatus.PREPARING
            plan.started_at = datetime.utcnow()
            experiment.actual_start = plan.started_at

            # Prepare: assign tasks to robots, validate readiness
            await self.assign_to_robots(plan, schedule_entries)

            # PREPARING -> RUNNING
            await self._transition(plan, ExecutionState.RUNNING)
            experiment.status = ExperimentStatus.RUNNING

            # Execute tasks respecting dependencies
            await self._execute_task_graph(plan)

            # Check for failures
            if plan.failed_tasks:
                await self._transition(plan, ExecutionState.ERROR)
                experiment.status = ExperimentStatus.FAILED
                logger.error(
                    f"Execution failed: {len(plan.failed_tasks)} tasks failed"
                )
            else:
                # RUNNING -> COMPLETING
                await self._transition(plan, ExecutionState.COMPLETING)
                experiment.status = ExperimentStatus.COMPLETING

                # Finalize: collect results, release equipment
                await self._finalize_execution(plan)

                # COMPLETING -> DONE
                await self._transition(plan, ExecutionState.DONE)
                experiment.status = ExperimentStatus.COMPLETED
                plan.completed_at = datetime.utcnow()
                experiment.actual_end = plan.completed_at

                logger.info(
                    f"Protocol execution complete: {plan.progress_pct}% "
                    f"({len(plan.tasks)} tasks)"
                )

        except Exception as e:
            logger.error(f"Execution error: {e}")
            await self._transition(plan, ExecutionState.ERROR)
            experiment.status = ExperimentStatus.FAILED
            raise

        return plan

    async def decompose_to_tasks(
        self,
        protocol: Protocol,
        experiment_id: str,
    ) -> List[RobotTask]:
        """
        Decompose a protocol into atomic robot tasks.

        Each protocol step may generate one or more tasks depending
        on the operation type. Complex steps (e.g., serial dilution)
        are broken into individual transfer operations.

        Args:
            protocol: The protocol to decompose.
            experiment_id: ID of the parent experiment.

        Returns:
            List of RobotTask objects forming a task DAG.
        """
        tasks: List[RobotTask] = []
        step_to_task_ids: Dict[str, List[str]] = {}

        for step in sorted(protocol.steps, key=lambda s: s.order):
            step_tasks = self._step_to_tasks(step, experiment_id)

            # Map dependencies from step level to task level
            for task in step_tasks:
                for dep_step_id in step.dependencies:
                    if dep_step_id in step_to_task_ids:
                        # Depend on all tasks from the dependency step
                        task.dependencies.extend(step_to_task_ids[dep_step_id])

            task_ids = [t.id for t in step_tasks]
            step_to_task_ids[step.id] = task_ids
            tasks.extend(step_tasks)

        logger.info(
            f"Decomposed {len(protocol.steps)} protocol steps into "
            f"{len(tasks)} tasks"
        )
        return tasks

    async def assign_to_robots(
        self,
        plan: ExecutionPlan,
        schedule_entries: Optional[List[ScheduleEntry]] = None,
    ) -> Dict[str, str]:
        """
        Assign tasks to available robots/instruments.

        Assignment strategy:
        1. Use pre-scheduled equipment if available
        2. Otherwise, find best available equipment by type
        3. Load balance across equivalent instruments

        Args:
            plan: The execution plan with tasks to assign.
            schedule_entries: Pre-scheduled equipment assignments.

        Returns:
            Dict mapping task_id to equipment_id.
        """
        assignments: Dict[str, str] = {}

        # Build lookup from schedule entries
        scheduled_equipment: Dict[str, str] = {}
        if schedule_entries:
            for entry in schedule_entries:
                scheduled_equipment[entry.step_id] = entry.equipment_id

        # Track load per equipment
        equipment_load: Dict[str, int] = {eid: 0 for eid in self._equipment}

        for task in plan.tasks:
            equipment_id = None

            # 1. Check scheduled assignment
            if task.step_id in scheduled_equipment:
                equipment_id = scheduled_equipment[task.step_id]

            # 2. Find best available equipment
            if equipment_id is None:
                equipment_id = self._find_best_equipment(
                    task.equipment_type, equipment_load
                )

            if equipment_id is None:
                logger.warning(
                    f"No equipment available for task {task.name} "
                    f"(type={task.equipment_type.value})"
                )
                task.status = TaskStatus.FAILED
                task.error = f"No {task.equipment_type.value} available"
                continue

            task.assigned_equipment_id = equipment_id
            task.status = TaskStatus.ASSIGNED
            assignments[task.id] = equipment_id
            equipment_load[equipment_id] = equipment_load.get(equipment_id, 0) + 1

            logger.debug(
                f"Assigned task '{task.name}' to equipment {equipment_id}"
            )

        logger.info(
            f"Assigned {len(assignments)}/{len(plan.tasks)} tasks to equipment"
        )
        return assignments

    async def monitor_execution(
        self,
        plan_id: str,
    ) -> Dict[str, Any]:
        """
        Get real-time execution monitoring data for a plan.

        Args:
            plan_id: ID of the execution plan to monitor.

        Returns:
            Dict with comprehensive execution status.
        """
        plan = self._plans.get(plan_id)
        if plan is None:
            return {"error": f"Plan {plan_id} not found"}

        # Task status summary
        status_counts: Dict[str, int] = {}
        for task in plan.tasks:
            status_name = task.status.value
            status_counts[status_name] = status_counts.get(status_name, 0) + 1

        # Equipment utilization
        equipment_tasks: Dict[str, List[str]] = {}
        for task in plan.tasks:
            if task.assigned_equipment_id:
                equipment_tasks.setdefault(
                    task.assigned_equipment_id, []
                ).append(task.id)

        # Timing
        elapsed = None
        if plan.started_at:
            end = plan.completed_at or datetime.utcnow()
            elapsed = (end - plan.started_at).total_seconds()

        # Estimated time remaining
        remaining_tasks = [
            t for t in plan.tasks
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)
        ]
        estimated_remaining = sum(
            t.estimated_duration.total_seconds() for t in remaining_tasks
        )

        return {
            "plan_id": plan_id,
            "state": plan.state.name,
            "progress_pct": plan.progress_pct,
            "total_tasks": len(plan.tasks),
            "task_status": status_counts,
            "running_tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "equipment_id": t.assigned_equipment_id,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                }
                for t in plan.running_tasks
            ],
            "pending_ready": len(plan.pending_tasks),
            "failed_tasks": [
                {"id": t.id, "name": t.name, "error": t.error}
                for t in plan.failed_tasks
            ],
            "equipment_assignments": {
                eid: len(tids) for eid, tids in equipment_tasks.items()
            },
            "elapsed_seconds": elapsed,
            "estimated_remaining_seconds": estimated_remaining,
            "started_at": plan.started_at.isoformat() if plan.started_at else None,
            "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
        }

    async def pause_execution(self, plan_id: str) -> bool:
        """Pause a running execution plan."""
        plan = self._plans.get(plan_id)
        if plan and plan.state == ExecutionState.RUNNING:
            await self._transition(plan, ExecutionState.PAUSED)
            logger.info(f"Paused execution plan {plan_id}")
            return True
        return False

    async def resume_execution(self, plan_id: str) -> bool:
        """Resume a paused execution plan."""
        plan = self._plans.get(plan_id)
        if plan and plan.state == ExecutionState.PAUSED:
            await self._transition(plan, ExecutionState.RUNNING)
            logger.info(f"Resumed execution plan {plan_id}")
            return True
        return False

    # ── Private methods ─────────────────────────────────────────────────

    def _step_to_tasks(
        self,
        step: ProtocolStep,
        experiment_id: str,
    ) -> List[RobotTask]:
        """Convert a protocol step into one or more robot tasks."""
        tasks: List[RobotTask] = []

        # Determine if step needs decomposition
        params = step.parameters

        if step.equipment_type == EquipmentType.LIQUID_HANDLER:
            # Liquid handling may need plate transport first
            if params.get("requires_plate_transport", False):
                transport_task = RobotTask(
                    experiment_id=experiment_id,
                    step_id=step.id,
                    name=f"Transport plate for {step.name}",
                    description="Move plate to liquid handler deck",
                    equipment_type=EquipmentType.ROBOTIC_ARM,
                    parameters={"action": "transport", "destination": "liquid_handler"},
                    estimated_duration=timedelta(minutes=1),
                )
                tasks.append(transport_task)

                # Main liquid handling task depends on transport
                main_task = RobotTask(
                    experiment_id=experiment_id,
                    step_id=step.id,
                    name=step.name,
                    description=step.description,
                    equipment_type=step.equipment_type,
                    parameters=step.parameters,
                    dependencies=[transport_task.id],
                    estimated_duration=step.duration,
                )
                tasks.append(main_task)
            else:
                tasks.append(
                    RobotTask(
                        experiment_id=experiment_id,
                        step_id=step.id,
                        name=step.name,
                        description=step.description,
                        equipment_type=step.equipment_type,
                        parameters=step.parameters,
                        estimated_duration=step.duration,
                    )
                )
        elif step.equipment_type == EquipmentType.THERMOCYCLER:
            # PCR may need lid heating step
            tasks.append(
                RobotTask(
                    experiment_id=experiment_id,
                    step_id=step.id,
                    name=step.name,
                    description=step.description,
                    equipment_type=step.equipment_type,
                    parameters=step.parameters,
                    estimated_duration=step.duration,
                )
            )
        else:
            # Default: one task per step
            tasks.append(
                RobotTask(
                    experiment_id=experiment_id,
                    step_id=step.id,
                    name=step.name,
                    description=step.description,
                    equipment_type=step.equipment_type,
                    parameters=step.parameters,
                    estimated_duration=step.duration,
                )
            )

        return tasks

    def _find_best_equipment(
        self,
        equipment_type: EquipmentType,
        load: Dict[str, int],
    ) -> Optional[str]:
        """Find the best available equipment of a given type (load-balanced)."""
        candidates: List[tuple] = []
        for eid, equip in self._equipment.items():
            if equip.equipment_type != equipment_type:
                continue
            status = self._equipment_status.get(eid, equip.status)
            if status in (EquipmentStatus.AVAILABLE, EquipmentStatus.BUSY):
                candidates.append((load.get(eid, 0), eid))

        if not candidates:
            return None

        # Pick least loaded
        candidates.sort()
        return candidates[0][1]

    async def _transition(
        self,
        plan: ExecutionPlan,
        new_state: ExecutionState,
    ) -> None:
        """Transition execution plan to a new state with validation."""
        old_state = plan.state
        valid_next = VALID_TRANSITIONS.get(old_state, set())

        if new_state not in valid_next:
            raise ValueError(
                f"Invalid state transition: {old_state.name} -> {new_state.name}. "
                f"Valid transitions: {[s.name for s in valid_next]}"
            )

        plan.state = new_state
        logger.info(f"Plan {plan.id}: {old_state.name} -> {new_state.name}")

        # Fire callbacks
        callbacks = self._state_callbacks.get(new_state, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(plan)
                else:
                    callback(plan)
            except Exception as e:
                logger.error(f"State callback error: {e}")

    async def _execute_task_graph(self, plan: ExecutionPlan) -> None:
        """Execute the task DAG, running independent tasks in parallel."""
        max_concurrent = 4  # Maximum parallel tasks

        while True:
            if plan.state == ExecutionState.PAUSED:
                await asyncio.sleep(1)
                continue

            ready = plan.pending_tasks
            running = plan.running_tasks

            if not ready and not running:
                break

            # Launch ready tasks up to concurrency limit
            slots_available = max_concurrent - len(running)
            to_launch = ready[:slots_available]

            if to_launch:
                launch_coros = [
                    self._execute_single_task(task) for task in to_launch
                ]
                await asyncio.gather(*launch_coros, return_exceptions=True)
            else:
                # Wait a bit for running tasks to complete
                await asyncio.sleep(0.1)

    async def _execute_single_task(self, task: RobotTask) -> None:
        """Execute a single task on its assigned equipment."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        try:
            if self._task_executor and task.assigned_equipment_id:
                equipment = self._equipment.get(task.assigned_equipment_id)
                if equipment:
                    result = await self._task_executor(task, equipment)
                    task.result = result

            # Simulate execution time for testing
            await asyncio.sleep(0.01)

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.actual_duration = task.completed_at - task.started_at

            logger.debug(f"Task '{task.name}' completed")

        except Exception as e:
            task.error = str(e)
            task.retry_count += 1

            if task.retry_count < task.max_retries:
                logger.warning(
                    f"Task '{task.name}' failed (attempt {task.retry_count}/"
                    f"{task.max_retries}): {e}"
                )
                task.status = TaskStatus.PENDING  # Re-queue for retry
            else:
                task.status = TaskStatus.FAILED
                logger.error(
                    f"Task '{task.name}' permanently failed after "
                    f"{task.max_retries} retries: {e}"
                )

    async def _finalize_execution(self, plan: ExecutionPlan) -> None:
        """Finalize execution: release equipment, collect results."""
        # Release equipment
        for task in plan.tasks:
            if task.assigned_equipment_id:
                self._equipment_status[task.assigned_equipment_id] = (
                    EquipmentStatus.AVAILABLE
                )

        # Compile execution summary
        total_duration = timedelta()
        for task in plan.tasks:
            if task.actual_duration:
                total_duration += task.actual_duration

        plan.metadata["total_task_duration"] = str(total_duration)
        plan.metadata["tasks_completed"] = sum(
            1 for t in plan.tasks if t.status == TaskStatus.COMPLETED
        )
        plan.metadata["tasks_failed"] = sum(
            1 for t in plan.tasks if t.status == TaskStatus.FAILED
        )

        logger.info(
            f"Execution finalized: {plan.metadata['tasks_completed']} completed, "
            f"{plan.metadata['tasks_failed']} failed"
        )
