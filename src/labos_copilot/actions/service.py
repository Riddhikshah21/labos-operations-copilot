"""Creation of validated mock operations actions."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from labos_copilot.domain import (
    ActionStatus,
    ActionType,
    BlockerCategory,
    OperationsAction,
)
from labos_copilot.rules import BlockerEngine

NowProvider = Callable[[], datetime]
ActionIdFactory = Callable[[], str]


class ActionPreparationError(ValueError):
    """Raised when a requested mock action is unsupported."""


_ACTION_TYPES = {
    BlockerCategory.DELAY: ActionType.REQUEST_OWNER_REVIEW,
    BlockerCategory.INVENTORY: ActionType.ESCALATE_MATERIAL_PROCUREMENT,
    BlockerCategory.INSTRUMENT: ActionType.REQUEST_INSTRUMENT_RESCHEDULE,
    BlockerCategory.DEADLINE: ActionType.ESCALATE_DELIVERY_RISK,
}


def utc_now() -> datetime:
    """Return the current UTC timestamp."""

    return datetime.now(UTC)


def generate_action_id() -> str:
    """Generate a display-friendly action identifier."""

    return f"ACT-{uuid4().hex[:12].upper()}"


class ActionService:
    """Prepare simulated actions from deterministic findings."""

    def __init__(
        self,
        engine: BlockerEngine,
        now_provider: NowProvider = utc_now,
        id_factory: ActionIdFactory = generate_action_id,
    ) -> None:
        self._engine = engine
        self._now_provider = now_provider
        self._id_factory = id_factory

    def prepare(
        self,
        experiment_id: str,
        rule_id: str,
        as_of: datetime | None = None,
    ) -> OperationsAction:
        """Create a mock action for an existing blocker finding."""

        analysis_time = as_of or self._now_provider()

        analysis = self._engine.analyze_experiment(
            experiment_id,
            analysis_time,
        )

        finding = next(
            (candidate for candidate in analysis.findings if candidate.rule_id == rule_id),
            None,
        )

        if finding is None:
            raise ActionPreparationError(
                f"No finding {rule_id!r} exists for experiment {experiment_id!r}."
            )

        action_type = _ACTION_TYPES[finding.category]

        return OperationsAction(
            id=self._id_factory(),
            experiment_id=experiment_id,
            source_rule_id=finding.rule_id,
            source_category=finding.category,
            action_type=action_type,
            status=ActionStatus.MOCK_COMPLETED,
            created_at=analysis_time,
            recommended_action=finding.recommended_action,
            evidence=finding.evidence,
        )
