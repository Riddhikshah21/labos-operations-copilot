"""Shared configuration for domain models."""

from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Base class for validated LabOS domain objects."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )
