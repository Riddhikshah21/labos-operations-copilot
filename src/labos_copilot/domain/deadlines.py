"""Customer deadline domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from labos_copilot.domain.base import DomainModel


class DeadlinePriority(StrEnum):
    """Business priority associated with a deadline."""

    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class CustomerDeadline(DomainModel):
    """Customer delivery deadline associated with an experiment."""

    id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    customer_name: str = Field(min_length=1)

    due_at: datetime
    priority: DeadlinePriority
