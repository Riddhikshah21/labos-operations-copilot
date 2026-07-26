"""Structured MCP tool responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from labos_copilot.domain import (
    CustomerDeadline,
    Experiment,
    ExperimentBlockerAnalysis,
    Instrument,
    InventoryItem,
)
from labos_copilot.domain.base import DomainModel


class ExperimentSummary(DomainModel):
    """Compact experiment representation for list operations."""

    id: str
    name: str
    status: str
    current_stage: str

    @classmethod
    def from_experiment(
        cls,
        experiment: Experiment,
    ) -> ExperimentSummary:
        return cls(
            id=experiment.id,
            name=experiment.name,
            status=experiment.status.value,
            current_stage=experiment.current_stage.value,
        )


class ActiveExperimentsResponse(DomainModel):
    """Response returned when listing active experiments."""

    count: int = Field(ge=0)
    experiments: tuple[ExperimentSummary, ...]


class ExperimentContext(DomainModel):
    """Experiment and its related operational records."""

    experiment: Experiment
    inventory: tuple[InventoryItem, ...]
    instrument: Instrument | None = None
    deadline: CustomerDeadline | None = None


class ActiveAnalysisResponse(DomainModel):
    """Blocker analysis for every active experiment."""

    as_of: datetime
    analyses: tuple[ExperimentBlockerAnalysis, ...]
