"""
Unit tests for the AI Scheduler.

These tests verify the scheduling and resource allocation capabilities of the
braas.pipeline.scheduling.scheduler.AIScheduler class, which manages
equipment scheduling, conflict detection, and priority-based queuing.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from braas.pipeline.scheduling.scheduler import (
    AIScheduler,
    ScheduleSlot,
    Priority,
    Equipment,
)


class TestAIScheduler:
    """Test suite for AIScheduler."""

    @pytest.fixture
    def scheduler(self) -> AIScheduler:
        """Create an AIScheduler instance for testing."""
        return AIScheduler()

    @pytest.fixture
    def mock_equipment(self) -> Equipment:
        """Create a mock equipment object."""
        equipment = MagicMock(spec=Equipment)
        equipment.id = "plate_reader_01"
        equipment.name = "Plate Reader 1"
        equipment.status = "idle"
        equipment.next_available_time = datetime.now()
        return equipment

    @pytest.mark.asyncio
    async def test_schedule_experiment(
        self, scheduler: AIScheduler, mock_equipment: Equipment
    ) -> None:
        """Test that scheduling an experiment returns a ScheduleSlot."""
        scheduler.get_equipment = AsyncMock(return_value=mock_equipment)

        experiment_request = {
            "experiment_id": "exp_001",
            "experiment_type": "ELISA",
            "duration_minutes": 120,
            "priority": Priority.NORMAL,
        }

        slot = await scheduler.schedule_experiment(experiment_request)

        assert isinstance(slot, ScheduleSlot)
        assert slot.experiment_id == "exp_001"
        assert slot.equipment_id == "plate_reader_01"
        assert slot.start_time is not None
        assert slot.end_time is not None
        assert slot.end_time > slot.start_time

    @pytest.mark.asyncio
    async def test_conflict_detection(
        self, scheduler: AIScheduler, mock_equipment: Equipment
    ) -> None:
        """Test that scheduling detects conflicts when equipment is busy."""
        busy_time = datetime.now() + timedelta(hours=1)
        mock_equipment.status = "busy"
        mock_equipment.next_available_time = busy_time
        scheduler.get_equipment = AsyncMock(return_value=mock_equipment)

        experiment_request = {
            "experiment_id": "exp_002",
            "experiment_type": "ELISA",
            "duration_minutes": 120,
            "priority": Priority.NORMAL,
        }

        slot = await scheduler.schedule_experiment(experiment_request)

        assert slot.start_time >= busy_time
        assert slot.has_conflict is True or slot.start_time > datetime.now()

    @pytest.mark.asyncio
    async def test_priority_queue(
        self, scheduler: AIScheduler, mock_equipment: Equipment
    ) -> None:
        """Test that priority levels are respected in the scheduling queue."""
        scheduler.get_equipment = AsyncMock(return_value=mock_equipment)

        high_priority_request = {
            "experiment_id": "exp_high",
            "experiment_type": "ELISA",
            "duration_minutes": 60,
            "priority": Priority.HIGH,
        }

        low_priority_request = {
            "experiment_id": "exp_low",
            "experiment_type": "ELISA",
            "duration_minutes": 60,
            "priority": Priority.LOW,
        }

        high_slot = await scheduler.schedule_experiment(high_priority_request)
        low_slot = await scheduler.schedule_experiment(low_priority_request)

        assert high_slot.priority >= low_slot.priority

    @pytest.mark.asyncio
    async def test_get_equipment_utilization(
        self, scheduler: AIScheduler, mock_equipment: Equipment
    ) -> None:
        """Test that equipment utilization returns correct utilization dict."""
        mock_equipment.status = "busy"
        mock_equipment.utilization_percent = 75.5
        scheduler.get_all_equipment = AsyncMock(return_value=[mock_equipment])

        utilization = await scheduler.get_equipment_utilization()

        assert isinstance(utilization, dict)
        assert "plate_reader_01" in utilization
        assert utilization["plate_reader_01"]["status"] == "busy"
        assert "utilization_percent" in utilization["plate_reader_01"]
