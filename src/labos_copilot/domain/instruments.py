"""Laboratory instrument domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from labos_copilot.domain.base import DomainModel


class InstrumentStatus(StrEnum):
    """Operational status of a laboratory instrument."""

    AVAILABLE = "available"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class Instrument(DomainModel):
    """A laboratory instrument used by experiments."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)

    status: InstrumentStatus
    current_experiment_id: str | None = None
    available_at: datetime | None = None
