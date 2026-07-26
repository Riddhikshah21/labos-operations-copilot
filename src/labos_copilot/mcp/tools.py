"""Application-facing implementations of MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from labos_copilot.domain import (
    CustomerDeadline,
    ExperimentBlockerAnalysis,
    Instrument,
    InventoryItem,
)
from labos_copilot.mcp.schemas import (
    ActiveAnalysisResponse,
    ActiveExperimentsResponse,
    ExperimentContext,
    ExperimentSummary,
)
from labos_copilot.rules import BlockerEngine
from labos_copilot.sdk import LabOSClient

NowProvider = Callable[[], datetime]


def utc_now() -> datetime:
    """Return the current UTC time."""

    return datetime.now(UTC)


class LabOSToolService:
    """Typed implementations backing the MCP server."""

    def __init__(
        self,
        client: LabOSClient,
        engine: BlockerEngine | None = None,
        now_provider: NowProvider = utc_now,
    ) -> None:
        self._client = client
        self._engine = engine or BlockerEngine(client)
        self._now_provider = now_provider

    def list_active_experiments(self) -> ActiveExperimentsResponse:
        """List active experiments using compact summaries."""

        experiments = tuple(
            ExperimentSummary.from_experiment(experiment)
            for experiment in self._client.experiments.list_active()
        )

        return ActiveExperimentsResponse(
            count=len(experiments),
            experiments=experiments,
        )

    def get_experiment_details(
        self,
        experiment_id: str,
    ) -> ExperimentContext:
        """Retrieve an experiment and its related records."""

        experiment = self._client.experiments.get(experiment_id)

        inventory = tuple(
            self._client.inventory.get(material_id)
            for material_id in experiment.required_material_ids
        )

        instrument = (
            self._client.instruments.get(
                experiment.required_instrument_id,
            )
            if experiment.required_instrument_id is not None
            else None
        )

        deadline = (
            self._client.deadlines.get(experiment.deadline_id)
            if experiment.deadline_id is not None
            else None
        )

        return ExperimentContext(
            experiment=experiment,
            inventory=inventory,
            instrument=instrument,
            deadline=deadline,
        )

    def get_inventory_status(
        self,
        material_id: str,
    ) -> InventoryItem:
        """Retrieve one inventory record."""

        return self._client.inventory.get(material_id)

    def get_instrument_status(
        self,
        instrument_id: str,
    ) -> Instrument:
        """Retrieve one instrument record."""

        return self._client.instruments.get(instrument_id)

    def get_customer_deadline(
        self,
        experiment_id: str,
    ) -> CustomerDeadline:
        """Retrieve the deadline associated with an experiment."""

        return self._client.deadlines.get_for_experiment(experiment_id)

    def analyze_experiment_blockers(
        self,
        experiment_id: str,
        as_of: datetime | None = None,
    ) -> ExperimentBlockerAnalysis:
        """Run deterministic blocker analysis for one experiment."""

        analysis_time = as_of or self._now_provider()

        return self._engine.analyze_experiment(
            experiment_id,
            analysis_time,
        )

    def analyze_active_experiments(
        self,
        as_of: datetime | None = None,
    ) -> ActiveAnalysisResponse:
        """Run deterministic blocker analysis for all active experiments."""

        analysis_time = as_of or self._now_provider()

        analyses = self._engine.analyze_active(analysis_time)

        return ActiveAnalysisResponse(
            as_of=analysis_time,
            analyses=tuple(analyses),
        )
