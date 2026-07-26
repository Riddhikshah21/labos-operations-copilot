"""Inventory domain models."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from labos_copilot.domain.base import DomainModel


class InventoryStatus(StrEnum):
    """Availability state for a laboratory material."""

    AVAILABLE = "available"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


class InventoryItem(DomainModel):
    """A material required by one or more experiments."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)

    status: InventoryStatus

    quantity: float = Field(ge=0)
    minimum_required: float = Field(ge=0)
    unit: str = Field(min_length=1)

    expected_restock_at: datetime | None = None
