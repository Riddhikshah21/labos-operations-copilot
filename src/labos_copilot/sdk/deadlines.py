"""Typed access to customer deadlines."""

from collections.abc import Iterable

from labos_copilot.domain import CustomerDeadline
from labos_copilot.sdk.errors import (
    DuplicateResourceError,
    ResourceNotFoundError,
)


class DeadlineService:
    """Read-only access to customer delivery deadlines."""

    def __init__(self, deadlines: Iterable[CustomerDeadline]) -> None:
        self._deadlines_by_id: dict[str, CustomerDeadline] = {}
        self._deadlines_by_experiment_id: dict[str, CustomerDeadline] = {}

        for deadline in deadlines:
            if deadline.id in self._deadlines_by_id:
                raise DuplicateResourceError(
                    resource_type="deadline",
                    resource_id=deadline.id,
                )

            if deadline.experiment_id in self._deadlines_by_experiment_id:
                raise DuplicateResourceError(
                    resource_type="experiment deadline",
                    resource_id=deadline.experiment_id,
                )

            self._deadlines_by_id[deadline.id] = deadline
            self._deadlines_by_experiment_id[deadline.experiment_id] = deadline

    def list_all(self) -> list[CustomerDeadline]:
        """Return all deadlines."""

        return list(self._deadlines_by_id.values())

    def get(self, deadline_id: str) -> CustomerDeadline:
        """Return a deadline by identifier."""

        try:
            return self._deadlines_by_id[deadline_id]
        except KeyError as exc:
            raise ResourceNotFoundError(
                resource_type="deadline",
                resource_id=deadline_id,
            ) from exc

    def get_for_experiment(self, experiment_id: str) -> CustomerDeadline:
        """Return the deadline associated with an experiment."""

        try:
            return self._deadlines_by_experiment_id[experiment_id]
        except KeyError as exc:
            raise ResourceNotFoundError(
                resource_type="experiment deadline",
                resource_id=experiment_id,
            ) from exc
