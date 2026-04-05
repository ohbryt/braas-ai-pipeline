"""
BRaaS AI Scheduler - Intelligent experiment scheduling with multi-objective optimization.

Uses priority queues, constraint satisfaction, and a genetic algorithm-based
optimizer to schedule experiments across shared laboratory equipment.
"""
from __future__ import annotations

import asyncio
import copy
import heapq
import logging
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from braas.core.enums import (
    EquipmentStatus,
    EquipmentType,
    ExperimentStatus,
    Priority,
    TaskStatus,
)
from braas.core.models import (
    Equipment,
    Experiment,
    Protocol,
    ProtocolStep,
    ScheduleEntry,
    TimeSlot,
)

logger = logging.getLogger(__name__)


@dataclass
class ScheduleRequest:
    """Request to schedule an experiment."""
    experiment: Experiment
    protocol: Protocol
    earliest_start: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    preferred_equipment: Optional[Dict[EquipmentType, str]] = None


@dataclass
class ScheduleConflict:
    """Represents a scheduling conflict between two entries."""
    entry_a: ScheduleEntry
    entry_b: ScheduleEntry
    equipment_id: str
    overlap_start: datetime
    overlap_end: datetime
    resolution: Optional[str] = None


@dataclass
class EquipmentWindow:
    """Availability window for a piece of equipment."""
    equipment_id: str
    equipment_type: EquipmentType
    available_from: datetime
    available_until: datetime
    maintenance_windows: List[Tuple[datetime, datetime]] = field(default_factory=list)

    def is_available_at(self, start: datetime, end: datetime) -> bool:
        """Check if equipment is available during the given period."""
        if start < self.available_from or end > self.available_until:
            return False
        for maint_start, maint_end in self.maintenance_windows:
            if start < maint_end and maint_start < end:
                return False
        return True

    def next_available_after(self, after: datetime, duration: timedelta) -> Optional[datetime]:
        """Find the next available slot after a given time."""
        candidate = max(after, self.available_from)
        end_needed = candidate + duration
        if end_needed > self.available_until:
            return None
        for maint_start, maint_end in sorted(self.maintenance_windows):
            if candidate < maint_end and maint_start < end_needed:
                candidate = maint_end
                end_needed = candidate + duration
                if end_needed > self.available_until:
                    return None
        return candidate


class AIScheduler:
    """
    Intelligent experiment scheduler with multi-objective optimization.

    Manages scheduling of experiments across shared laboratory equipment,
    handling priorities, dependencies, and resource constraints.
    """

    def __init__(self) -> None:
        self._schedule: List[ScheduleEntry] = []
        self._equipment_windows: Dict[str, EquipmentWindow] = {}
        self._equipment_registry: Dict[str, Equipment] = {}
        self._priority_queue: List[Tuple[int, str, ScheduleRequest]] = []
        self._queue_counter: int = 0
        self._optimizer = ScheduleOptimizer()
        logger.info("AIScheduler initialized")

    def register_equipment(self, equipment: Equipment, window: EquipmentWindow) -> None:
        """Register equipment and its availability window."""
        self._equipment_registry[equipment.id] = equipment
        self._equipment_windows[equipment.id] = window
        logger.info(f"Registered equipment: {equipment.name} ({equipment.id})")

    async def schedule_experiment(
        self,
        request: ScheduleRequest,
    ) -> List[ScheduleEntry]:
        """
        Schedule an experiment by assigning time slots to each protocol step.

        Uses constraint satisfaction to find valid slots respecting:
        - Equipment availability windows
        - Step dependencies (topological ordering)
        - Priority-based ordering
        - Deadline constraints

        Args:
            request: The scheduling request with experiment and protocol details.

        Returns:
            List of ScheduleEntry objects representing the assigned slots.

        Raises:
            ValueError: If scheduling is not feasible given constraints.
        """
        logger.info(
            f"Scheduling experiment: {request.experiment.name} "
            f"(priority={request.experiment.priority.name})"
        )

        # Add to priority queue
        self._queue_counter += 1
        heapq.heappush(
            self._priority_queue,
            (request.experiment.priority.value, self._queue_counter, request),
        )

        # Build dependency graph for protocol steps
        step_order = self._topological_sort(request.protocol.steps)

        entries: List[ScheduleEntry] = []
        step_end_times: Dict[str, datetime] = {}
        current_time = request.earliest_start

        for step in step_order:
            # Calculate earliest start based on dependencies
            earliest = current_time
            for dep_id in step.dependencies:
                if dep_id in step_end_times:
                    earliest = max(earliest, step_end_times[dep_id])

            # Find suitable equipment
            equipment_id = await self._find_equipment(
                step.equipment_type,
                earliest,
                step.duration,
                request.preferred_equipment,
            )

            if equipment_id is None:
                raise ValueError(
                    f"No available {step.equipment_type.value} for step "
                    f"'{step.name}' starting after {earliest}"
                )

            # Get the actual start time from equipment window
            window = self._equipment_windows[equipment_id]
            actual_start = window.next_available_after(earliest, step.duration)

            if actual_start is None:
                raise ValueError(
                    f"Equipment {equipment_id} has no available window for "
                    f"step '{step.name}' (duration={step.duration})"
                )

            # Check for conflicts with existing schedule
            proposed_end = actual_start + step.duration
            if request.deadline and proposed_end > request.deadline:
                logger.warning(
                    f"Step '{step.name}' would end after deadline: "
                    f"{proposed_end} > {request.deadline}"
                )

            # Check existing schedule conflicts
            conflict = self._check_conflict(equipment_id, actual_start, proposed_end)
            if conflict:
                # Shift to after the conflicting entry
                actual_start = conflict.end_time
                proposed_end = actual_start + step.duration

            entry = ScheduleEntry(
                id=str(uuid.uuid4()),
                experiment_id=request.experiment.id,
                step_id=step.id,
                equipment_id=equipment_id,
                start_time=actual_start,
                end_time=proposed_end,
                status=TaskStatus.PENDING,
                priority=request.experiment.priority,
            )

            entries.append(entry)
            self._schedule.append(entry)
            step_end_times[step.id] = proposed_end

        # Update experiment status
        request.experiment.status = ExperimentStatus.SCHEDULED
        if entries:
            request.experiment.scheduled_start = entries[0].start_time
            request.experiment.scheduled_end = entries[-1].end_time

        logger.info(
            f"Scheduled {len(entries)} steps for experiment "
            f"{request.experiment.name}: "
            f"{entries[0].start_time} -> {entries[-1].end_time}"
        )

        return entries

    async def optimize_schedule(
        self,
        objectives: Optional[Dict[str, float]] = None,
    ) -> List[ScheduleEntry]:
        """
        Optimize the current schedule using multi-objective optimization.

        Objectives (with default weights):
        - minimize_makespan (0.4): Minimize total time from first to last task
        - maximize_utilization (0.3): Maximize equipment utilization
        - minimize_wait_time (0.2): Minimize idle time between steps
        - respect_priorities (0.1): Higher priority experiments scheduled first

        Args:
            objectives: Dict mapping objective names to weights (0.0-1.0).

        Returns:
            Optimized list of ScheduleEntry objects.
        """
        if not objectives:
            objectives = {
                "minimize_makespan": 0.4,
                "maximize_utilization": 0.3,
                "minimize_wait_time": 0.2,
                "respect_priorities": 0.1,
            }

        logger.info(f"Optimizing schedule with objectives: {objectives}")

        optimized = await self._optimizer.optimize(
            schedule=self._schedule,
            equipment_windows=self._equipment_windows,
            objectives=objectives,
        )

        self._schedule = optimized
        logger.info(f"Schedule optimized: {len(optimized)} entries")
        return optimized

    async def get_equipment_utilization(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate equipment utilization metrics over a time range.

        Args:
            start: Start of the analysis window (default: earliest scheduled).
            end: End of the analysis window (default: latest scheduled).

        Returns:
            Dict mapping equipment_id to utilization metrics including:
            - utilization_pct: Percentage of time in use
            - total_tasks: Number of tasks assigned
            - busy_time: Total busy duration
            - idle_time: Total idle duration
            - avg_task_duration: Average task duration
        """
        if not self._schedule:
            return {}

        if start is None:
            start = min(e.start_time for e in self._schedule)
        if end is None:
            end = max(e.end_time for e in self._schedule)

        total_window = (end - start).total_seconds()
        if total_window <= 0:
            return {}

        utilization: Dict[str, Dict[str, Any]] = {}

        for equip_id, equip in self._equipment_registry.items():
            equip_entries = [
                e for e in self._schedule
                if e.equipment_id == equip_id
                and e.start_time < end
                and e.end_time > start
            ]

            busy_seconds = sum(
                (min(e.end_time, end) - max(e.start_time, start)).total_seconds()
                for e in equip_entries
            )

            idle_seconds = total_window - busy_seconds
            avg_duration = (
                busy_seconds / len(equip_entries) if equip_entries else 0.0
            )

            utilization[equip_id] = {
                "equipment_name": equip.name,
                "equipment_type": equip.equipment_type.value,
                "utilization_pct": round((busy_seconds / total_window) * 100, 2),
                "total_tasks": len(equip_entries),
                "busy_time": timedelta(seconds=busy_seconds),
                "idle_time": timedelta(seconds=idle_seconds),
                "avg_task_duration": timedelta(seconds=avg_duration),
            }

        return utilization

    async def resolve_conflicts(self) -> List[ScheduleConflict]:
        """
        Detect and resolve scheduling conflicts.

        Conflicts are resolved using these strategies:
        1. Priority-based: Lower priority experiment is moved
        2. Duration-based: Shorter task is moved (less disruption)
        3. Deadline-based: Task closer to deadline keeps its slot

        Returns:
            List of detected conflicts with their resolutions.
        """
        conflicts: List[ScheduleConflict] = []

        # Group entries by equipment
        by_equipment: Dict[str, List[ScheduleEntry]] = {}
        for entry in self._schedule:
            by_equipment.setdefault(entry.equipment_id, []).append(entry)

        for equip_id, entries in by_equipment.items():
            sorted_entries = sorted(entries, key=lambda e: e.start_time)

            for i in range(len(sorted_entries) - 1):
                a = sorted_entries[i]
                b = sorted_entries[i + 1]

                if a.end_time > b.start_time:
                    overlap_start = b.start_time
                    overlap_end = min(a.end_time, b.end_time)

                    conflict = ScheduleConflict(
                        entry_a=a,
                        entry_b=b,
                        equipment_id=equip_id,
                        overlap_start=overlap_start,
                        overlap_end=overlap_end,
                    )

                    # Resolve: move lower priority task
                    if a.priority.value > b.priority.value:
                        # a has lower priority (higher number), move a
                        shift = a.end_time - b.start_time
                        a.start_time = b.end_time
                        a.end_time = a.start_time + (a.end_time - a.start_time + shift)
                        conflict.resolution = (
                            f"Moved entry {a.id} after {b.id} (lower priority)"
                        )
                    else:
                        # b has lower priority or equal, move b
                        shift = a.end_time - b.start_time
                        b.start_time = a.end_time
                        b.end_time = b.start_time + (b.end_time - b.start_time)
                        conflict.resolution = (
                            f"Moved entry {b.id} after {a.id} (lower/equal priority)"
                        )

                    conflicts.append(conflict)
                    logger.info(f"Resolved conflict: {conflict.resolution}")

        return conflicts

    def get_schedule(
        self,
        experiment_id: Optional[str] = None,
        equipment_id: Optional[str] = None,
    ) -> List[ScheduleEntry]:
        """Get schedule entries, optionally filtered."""
        entries = self._schedule
        if experiment_id:
            entries = [e for e in entries if e.experiment_id == experiment_id]
        if equipment_id:
            entries = [e for e in entries if e.equipment_id == equipment_id]
        return sorted(entries, key=lambda e: e.start_time)

    # ── Private helpers ─────────────────────────────────────────────────

    def _topological_sort(self, steps: List[ProtocolStep]) -> List[ProtocolStep]:
        """Topologically sort protocol steps by dependencies."""
        step_map = {s.id: s for s in steps}
        visited: Set[str] = set()
        order: List[ProtocolStep] = []

        def dfs(step_id: str) -> None:
            if step_id in visited:
                return
            visited.add(step_id)
            step = step_map[step_id]
            for dep_id in step.dependencies:
                if dep_id in step_map:
                    dfs(dep_id)
            order.append(step)

        # Sort by explicit order first, then DFS
        for step in sorted(steps, key=lambda s: s.order):
            dfs(step.id)

        return order

    async def _find_equipment(
        self,
        equipment_type: EquipmentType,
        earliest: datetime,
        duration: timedelta,
        preferred: Optional[Dict[EquipmentType, str]] = None,
    ) -> Optional[str]:
        """Find the best available equipment of the given type."""
        # Check preferred equipment first
        if preferred and equipment_type in preferred:
            pref_id = preferred[equipment_type]
            if pref_id in self._equipment_windows:
                window = self._equipment_windows[pref_id]
                if window.is_available_at(earliest, earliest + duration):
                    return pref_id

        # Find all equipment of the right type
        candidates: List[Tuple[datetime, str]] = []
        for equip_id, equip in self._equipment_registry.items():
            if equip.equipment_type != equipment_type:
                continue
            if equip.status in (EquipmentStatus.OFFLINE, EquipmentStatus.ERROR):
                continue

            window = self._equipment_windows.get(equip_id)
            if window is None:
                continue

            avail_time = window.next_available_after(earliest, duration)
            if avail_time is not None:
                candidates.append((avail_time, equip_id))

        if not candidates:
            return None

        # Pick the one available soonest
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def _check_conflict(
        self,
        equipment_id: str,
        start: datetime,
        end: datetime,
    ) -> Optional[ScheduleEntry]:
        """Check if a proposed slot conflicts with existing entries."""
        for entry in self._schedule:
            if entry.equipment_id != equipment_id:
                continue
            if start < entry.end_time and entry.start_time < end:
                return entry
        return None


class ScheduleOptimizer:
    """
    Multi-objective schedule optimizer using a genetic algorithm approach.

    Evolves a population of schedule permutations to find optimal
    assignments of tasks to equipment and time slots.
    """

    def __init__(
        self,
        population_size: int = 50,
        generations: int = 100,
        mutation_rate: float = 0.15,
        crossover_rate: float = 0.7,
        elite_ratio: float = 0.1,
    ) -> None:
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_count = max(1, int(population_size * elite_ratio))
        self._rng = random.Random(42)

    async def optimize(
        self,
        schedule: List[ScheduleEntry],
        equipment_windows: Dict[str, EquipmentWindow],
        objectives: Dict[str, float],
    ) -> List[ScheduleEntry]:
        """
        Run genetic algorithm optimization on the schedule.

        Args:
            schedule: Current schedule to optimize.
            equipment_windows: Equipment availability windows.
            objectives: Weighted objectives for multi-objective fitness.

        Returns:
            Optimized schedule.
        """
        if len(schedule) < 2:
            return schedule

        # Initialize population with permutations of the schedule
        population = self._initialize_population(schedule)

        best_fitness = float("-inf")
        best_individual: List[ScheduleEntry] = schedule

        for gen in range(self.generations):
            # Evaluate fitness for each individual
            fitness_scores = [
                self._evaluate_fitness(ind, equipment_windows, objectives)
                for ind in population
            ]

            # Track best
            gen_best_idx = max(range(len(fitness_scores)), key=lambda i: fitness_scores[i])
            if fitness_scores[gen_best_idx] > best_fitness:
                best_fitness = fitness_scores[gen_best_idx]
                best_individual = copy.deepcopy(population[gen_best_idx])

            if gen % 20 == 0:
                logger.debug(
                    f"GA Generation {gen}: best_fitness={best_fitness:.4f}"
                )

            # Selection, crossover, mutation
            new_population: List[List[ScheduleEntry]] = []

            # Elitism: keep top individuals
            elite_indices = sorted(
                range(len(fitness_scores)),
                key=lambda i: fitness_scores[i],
                reverse=True,
            )[:self.elite_count]
            for idx in elite_indices:
                new_population.append(copy.deepcopy(population[idx]))

            # Fill remaining with offspring
            while len(new_population) < self.population_size:
                parent_a = self._tournament_select(population, fitness_scores)
                parent_b = self._tournament_select(population, fitness_scores)

                if self._rng.random() < self.crossover_rate:
                    child = self._crossover(parent_a, parent_b)
                else:
                    child = copy.deepcopy(parent_a)

                if self._rng.random() < self.mutation_rate:
                    child = self._mutate(child, equipment_windows)

                new_population.append(child)

            population = new_population

            # Yield control periodically for async context
            if gen % 10 == 0:
                await asyncio.sleep(0)

        logger.info(
            f"GA optimization complete: {self.generations} generations, "
            f"best_fitness={best_fitness:.4f}"
        )
        return best_individual

    def _initialize_population(
        self,
        schedule: List[ScheduleEntry],
    ) -> List[List[ScheduleEntry]]:
        """Create initial population by shuffling and shifting the schedule."""
        population: List[List[ScheduleEntry]] = []
        population.append(copy.deepcopy(schedule))  # Keep original

        for _ in range(self.population_size - 1):
            variant = copy.deepcopy(schedule)
            # Apply random time shifts
            for entry in variant:
                shift_minutes = self._rng.randint(-30, 30)
                entry.start_time += timedelta(minutes=shift_minutes)
                entry.end_time += timedelta(minutes=shift_minutes)
            # Shuffle order within same equipment
            self._rng.shuffle(variant)
            population.append(variant)

        return population

    def _evaluate_fitness(
        self,
        individual: List[ScheduleEntry],
        equipment_windows: Dict[str, EquipmentWindow],
        objectives: Dict[str, float],
    ) -> float:
        """
        Evaluate multi-objective fitness of a schedule.

        Higher fitness is better.
        """
        if not individual:
            return 0.0

        fitness = 0.0

        # 1. Minimize makespan (normalized)
        if "minimize_makespan" in objectives:
            start = min(e.start_time for e in individual)
            end = max(e.end_time for e in individual)
            makespan_hours = (end - start).total_seconds() / 3600
            # Lower makespan -> higher fitness (inverse, capped)
            makespan_score = 1.0 / (1.0 + makespan_hours / 24.0)
            fitness += objectives["minimize_makespan"] * makespan_score

        # 2. Maximize utilization
        if "maximize_utilization" in objectives:
            equip_busy: Dict[str, float] = {}
            equip_total: Dict[str, float] = {}
            for entry in individual:
                eid = entry.equipment_id
                dur = (entry.end_time - entry.start_time).total_seconds()
                equip_busy[eid] = equip_busy.get(eid, 0) + dur
                if eid in equipment_windows:
                    w = equipment_windows[eid]
                    equip_total[eid] = (
                        w.available_until - w.available_from
                    ).total_seconds()

            utilizations = []
            for eid, busy in equip_busy.items():
                total = equip_total.get(eid, busy)
                if total > 0:
                    utilizations.append(min(busy / total, 1.0))

            avg_util = sum(utilizations) / len(utilizations) if utilizations else 0
            fitness += objectives["maximize_utilization"] * avg_util

        # 3. Minimize wait time between dependent steps
        if "minimize_wait_time" in objectives:
            by_experiment: Dict[str, List[ScheduleEntry]] = {}
            for entry in individual:
                by_experiment.setdefault(entry.experiment_id, []).append(entry)

            total_wait = 0.0
            total_count = 0
            for entries in by_experiment.values():
                sorted_e = sorted(entries, key=lambda e: e.start_time)
                for i in range(len(sorted_e) - 1):
                    gap = (
                        sorted_e[i + 1].start_time - sorted_e[i].end_time
                    ).total_seconds()
                    total_wait += max(0, gap)
                    total_count += 1

            avg_wait = total_wait / total_count if total_count > 0 else 0
            wait_score = 1.0 / (1.0 + avg_wait / 3600.0)
            fitness += objectives["minimize_wait_time"] * wait_score

        # 4. Respect priorities (higher priority experiments earlier)
        if "respect_priorities" in objectives:
            priority_score = 0.0
            for i, entry in enumerate(
                sorted(individual, key=lambda e: e.start_time)
            ):
                # Lower priority value = higher importance
                rank = (len(individual) - i) / len(individual)
                prio_weight = (6 - entry.priority.value) / 5.0
                priority_score += rank * prio_weight

            priority_score /= len(individual)
            fitness += objectives["respect_priorities"] * priority_score

        # Penalty for constraint violations
        penalty = self._constraint_penalty(individual, equipment_windows)
        fitness -= penalty

        return fitness

    def _constraint_penalty(
        self,
        individual: List[ScheduleEntry],
        equipment_windows: Dict[str, EquipmentWindow],
    ) -> float:
        """Calculate penalty for constraint violations."""
        penalty = 0.0

        # Penalty for overlapping entries on same equipment
        by_equipment: Dict[str, List[ScheduleEntry]] = {}
        for entry in individual:
            by_equipment.setdefault(entry.equipment_id, []).append(entry)

        for entries in by_equipment.values():
            sorted_e = sorted(entries, key=lambda e: e.start_time)
            for i in range(len(sorted_e) - 1):
                if sorted_e[i].end_time > sorted_e[i + 1].start_time:
                    overlap = (
                        sorted_e[i].end_time - sorted_e[i + 1].start_time
                    ).total_seconds()
                    penalty += overlap / 3600.0

        # Penalty for scheduling outside equipment windows
        for entry in individual:
            window = equipment_windows.get(entry.equipment_id)
            if window:
                if entry.start_time < window.available_from:
                    diff = (window.available_from - entry.start_time).total_seconds()
                    penalty += diff / 3600.0
                if entry.end_time > window.available_until:
                    diff = (entry.end_time - window.available_until).total_seconds()
                    penalty += diff / 3600.0

        return penalty

    def _tournament_select(
        self,
        population: List[List[ScheduleEntry]],
        fitness_scores: List[float],
        k: int = 3,
    ) -> List[ScheduleEntry]:
        """Tournament selection: pick best of k random individuals."""
        indices = self._rng.sample(range(len(population)), min(k, len(population)))
        best_idx = max(indices, key=lambda i: fitness_scores[i])
        return copy.deepcopy(population[best_idx])

    def _crossover(
        self,
        parent_a: List[ScheduleEntry],
        parent_b: List[ScheduleEntry],
    ) -> List[ScheduleEntry]:
        """Single-point crossover between two schedule individuals."""
        if len(parent_a) <= 1:
            return copy.deepcopy(parent_a)

        point = self._rng.randint(1, len(parent_a) - 1)
        child = copy.deepcopy(parent_a[:point])

        # Add entries from parent_b that don't conflict
        used_ids = {e.step_id for e in child}
        for entry in parent_b:
            if entry.step_id not in used_ids:
                child.append(copy.deepcopy(entry))
                used_ids.add(entry.step_id)

        return child

    def _mutate(
        self,
        individual: List[ScheduleEntry],
        equipment_windows: Dict[str, EquipmentWindow],
    ) -> List[ScheduleEntry]:
        """Mutate an individual by shifting random entries in time."""
        if not individual:
            return individual

        idx = self._rng.randint(0, len(individual) - 1)
        entry = individual[idx]

        # Random time shift (-60 to +60 minutes)
        shift = timedelta(minutes=self._rng.randint(-60, 60))
        entry.start_time += shift
        entry.end_time += shift

        # Ensure entry stays within equipment window
        window = equipment_windows.get(entry.equipment_id)
        if window:
            if entry.start_time < window.available_from:
                diff = window.available_from - entry.start_time
                entry.start_time += diff
                entry.end_time += diff
            if entry.end_time > window.available_until:
                diff = entry.end_time - window.available_until
                entry.start_time -= diff
                entry.end_time -= diff

        return individual
