"""Experiment management routes."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class ExperimentStatus(str, Enum):
    """Experiment status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExperimentRequest(BaseModel):
    """Experiment submission request."""

    experiment_type: str = Field(..., description="Type of experiment: ELISA, qPCR, cell_culture")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Experiment parameters")
    priority: int = Field(default=5, ge=1, le=10, description="Priority (1=highest, 10=lowest)")


class ExperimentResponse(BaseModel):
    """Experiment response model."""

    id: str
    experiment_type: str
    status: ExperimentStatus
    created_at: datetime
    updated_at: datetime
    parameters: dict[str, Any]
    priority: int
    result: dict[str, Any] | None = None
    error: str | None = None


# In-memory store for demo purposes
experiments_store: dict[str, ExperimentResponse] = {}


@router.post("/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def submit_experiment(request: ExperimentRequest) -> ExperimentResponse:
    """Submit a new experiment.

    Args:
        request: Experiment submission request containing type, parameters, and priority.

    Returns:
        Created experiment with assigned ID and initial status.
    """
    experiment_id = str(uuid4())
    now = datetime.utcnow()

    experiment = ExperimentResponse(
        id=experiment_id,
        experiment_type=request.experiment_type,
        status=ExperimentStatus.PENDING,
        created_at=now,
        updated_at=now,
        parameters=request.parameters,
        priority=request.priority,
    )

    experiments_store[experiment_id] = experiment
    return experiment


@router.get("/", response_model=list[ExperimentResponse])
async def list_experiments() -> list[ExperimentResponse]:
    """List all experiments.

    Returns:
        List of all experiments in the store.
    """
    return list(experiments_store.values())


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(experiment_id: str) -> ExperimentResponse:
    """Get experiment status by ID.

    Args:
        experiment_id: Unique experiment identifier.

    Returns:
        Experiment details and current status.

    Raises:
        HTTPException: If experiment not found.
    """
    if experiment_id not in experiments_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    return experiments_store[experiment_id]


@router.get("/{experiment_id}/results", response_model=dict[str, Any])
async def get_experiment_results(experiment_id: str) -> dict[str, Any]:
    """Get experiment results by ID.

    Args:
        experiment_id: Unique experiment identifier.

    Returns:
        Experiment results if completed.

    Raises:
        HTTPException: If experiment not found or not completed.
    """
    if experiment_id not in experiments_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    experiment = experiments_store[experiment_id]

    if experiment.status != ExperimentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Experiment not completed. Current status: {experiment.status.value}",
        )

    if experiment.result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Results not available")

    return experiment.result


@router.post("/{experiment_id}/cancel", response_model=ExperimentResponse)
async def cancel_experiment(experiment_id: str) -> ExperimentResponse:
    """Cancel a running or pending experiment.

    Args:
        experiment_id: Unique experiment identifier.

    Returns:
        Updated experiment with cancelled status.

    Raises:
        HTTPException: If experiment not found or already completed.
    """
    if experiment_id not in experiments_store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    experiment = experiments_store[experiment_id]

    if experiment.status in (ExperimentStatus.COMPLETED, ExperimentStatus.FAILED, ExperimentStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel experiment in {experiment.status.value} state",
        )

    experiment.status = ExperimentStatus.CANCELLED
    experiment.updated_at = datetime.utcnow()
    experiments_store[experiment_id] = experiment

    return experiment
