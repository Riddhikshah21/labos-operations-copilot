"""Schemas used by the evaluation suite."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from labos_copilot.domain import (
    ActionType,
    BlockerCategory,
    Severity,
)
from labos_copilot.domain.base import DomainModel


class ExpectedFinding(DomainModel):
    """Expected deterministic blocker finding."""

    rule_id: str = Field(min_length=1)
    category: BlockerCategory
    severity: Severity


class AnalysisEvaluationCase(DomainModel):
    """Evaluation case for blocker analysis."""

    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    as_of: datetime

    expected_healthy: bool | None = None
    expected_findings: tuple[ExpectedFinding, ...] = ()
    expected_error_type: str | None = None


class ActionEvaluationCase(DomainModel):
    """Evaluation case for mock-action preparation."""

    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    as_of: datetime

    expected_action_type: ActionType | None = None
    expected_error_type: str | None = None


class EvaluationSuite(DomainModel):
    """Complete offline evaluation suite."""

    analysis_cases: tuple[AnalysisEvaluationCase, ...]
    action_cases: tuple[ActionEvaluationCase, ...]


class EvaluationCaseResult(DomainModel):
    """Result of one offline evaluation case."""

    case_id: str
    kind: Literal["analysis", "action"]
    passed: bool
    errors: tuple[str, ...] = ()
    observations: tuple[str, ...] = ()

    expected_findings: int = Field(default=0, ge=0)
    actual_findings: int = Field(default=0, ge=0)
    matched_findings: int = Field(default=0, ge=0)
    missing_findings: int = Field(default=0, ge=0)
    unexpected_findings: int = Field(default=0, ge=0)


class LiveAgentEvaluationResult(DomainModel):
    """Result of one optional live-agent evaluation."""

    case_id: str
    passed: bool
    errors: tuple[str, ...] = ()
    tools_used: tuple[str, ...] = ()
    approval_decisions: tuple[str, ...] = ()


class EvaluationSummary(DomainModel):
    """Aggregate offline evaluation metrics."""

    generated_at: datetime
    fixture_directory: str

    total_cases: int = Field(ge=0)
    passed_cases: int = Field(ge=0)
    failed_cases: int = Field(ge=0)
    pass_rate: float = Field(ge=0, le=1)

    expected_findings: int = Field(ge=0)
    matched_findings: int = Field(ge=0)
    missing_findings: int = Field(ge=0)
    unexpected_findings: int = Field(ge=0)

    finding_precision: float = Field(ge=0, le=1)
    finding_recall: float = Field(ge=0, le=1)

    results: tuple[EvaluationCaseResult, ...]
