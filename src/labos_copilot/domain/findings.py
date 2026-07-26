"""Operational blocker findings."""

from enum import StrEnum

from pydantic import Field

from labos_copilot.domain.base import DomainModel


class BlockerCategory(StrEnum):
    """Supported operational blocker categories."""

    DELAY = "delay"
    INVENTORY = "inventory"
    INSTRUMENT = "instrument"
    DEADLINE = "deadline"


class Severity(StrEnum):
    """Operational severity level."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class BlockerFinding(DomainModel):
    """A deterministic operational finding."""

    rule_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    category: BlockerCategory
    severity: Severity
    summary: str = Field(min_length=1)
    evidence: tuple[str, ...] = Field(min_length=1)
    recommended_action: str = Field(min_length=1)


class ExperimentBlockerAnalysis(DomainModel):
    """Complete blocker analysis for one experiment."""

    experiment_id: str = Field(min_length=1)
    findings: tuple[BlockerFinding, ...] = ()

    @property
    def is_healthy(self) -> bool:
        """Return whether no blockers were detected."""

        return not self.findings
