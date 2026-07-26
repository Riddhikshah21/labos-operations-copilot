"""Approval-gated mock operations actions."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from labos_copilot.domain.base import DomainModel
from labos_copilot.domain.findings import BlockerCategory


class ActionType(StrEnum):
    """Supported simulated operational actions."""

    REQUEST_OWNER_REVIEW = "request_owner_review"
    ESCALATE_MATERIAL_PROCUREMENT = "escalate_material_procurement"
    REQUEST_INSTRUMENT_RESCHEDULE = "request_instrument_reschedule"
    ESCALATE_DELIVERY_RISK = "escalate_delivery_risk"


class ActionStatus(StrEnum):
    """Execution status for a mock action."""

    MOCK_COMPLETED = "mock_completed"


class OperationsAction(DomainModel):
    """A simulated action created after human approval."""

    id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    source_rule_id: str = Field(min_length=1)
    source_category: BlockerCategory

    action_type: ActionType
    status: ActionStatus
    created_at: datetime

    recommended_action: str = Field(min_length=1)
    evidence: tuple[str, ...] = Field(min_length=1)

    disclaimer: str = "Simulation only. No external system or laboratory operation was changed."
