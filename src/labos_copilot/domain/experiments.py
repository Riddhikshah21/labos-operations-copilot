"""Experiment domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from labos_copilot.domain.base import DomainModel


class ExperimentStatus(StrEnum):
    """High-level experiment lifecycle status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentStage(StrEnum):
    """Simplified laboratory workflow stages."""

    QUEUED = "queued"
    WAITING_FOR_MATERIALS = "waiting_for_materials"
    RUNNING = "running"
    DATA_PROCESSING = "data_processing"
    REVIEW = "review"


class Experiment(DomainModel):
    """An experiment currently managed by the laboratory."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)

    status: ExperimentStatus
    current_stage: ExperimentStage

    stage_started_at: datetime
    expected_stage_duration_hours: float = Field(gt=0)

    required_material_ids: list[str] = Field(default_factory=list)
    required_instrument_id: str | None = None
    deadline_id: str | None = None
