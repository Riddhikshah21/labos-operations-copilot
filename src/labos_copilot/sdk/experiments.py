"""Typed access to experiment records."""

from collections.abc import Iterable

from labos_copilot.domain import Experiment, ExperimentStatus
from labos_copilot.sdk.errors import (
    DuplicateResourceError,
    ResourceNotFoundError,
)


class ExperimentService:
    """Read-only access to laboratory experiments."""

    def __init__(self, experiments: Iterable[Experiment]) -> None:
        self._experiments_by_id: dict[str, Experiment] = {}

        for experiment in experiments:
            if experiment.id in self._experiments_by_id:
                raise DuplicateResourceError(
                    resource_type="experiment",
                    resource_id=experiment.id,
                )

            self._experiments_by_id[experiment.id] = experiment

    def list_all(self) -> list[Experiment]:
        """Return every experiment."""

        return list(self._experiments_by_id.values())

    def list_active(self) -> list[Experiment]:
        """Return experiments currently marked as active."""

        return [
            experiment
            for experiment in self._experiments_by_id.values()
            if experiment.status is ExperimentStatus.ACTIVE
        ]

    def get(self, experiment_id: str) -> Experiment:
        """Return one experiment by identifier."""

        try:
            return self._experiments_by_id[experiment_id]
        except KeyError as exc:
            raise ResourceNotFoundError(
                resource_type="experiment",
                resource_id=experiment_id,
            ) from exc
