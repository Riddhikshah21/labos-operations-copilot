"""Validate LLM output against deterministic blocker analysis."""

from collections.abc import Iterable
from datetime import datetime

from labos_copilot.agent.errors import AgentGroundingError
from labos_copilot.agent.schemas import BriefItem, OperationsBrief
from labos_copilot.domain import (
    BlockerFinding,
    ExperimentBlockerAnalysis,
    Severity,
)


def _finding_signature(
    finding: BlockerFinding,
) -> tuple[object, ...]:
    return (
        finding.rule_id,
        finding.experiment_id,
        finding.category,
        finding.severity,
        finding.summary,
        finding.evidence,
        finding.recommended_action,
    )


def _brief_item_signature(
    item: BriefItem,
) -> tuple[object, ...]:
    return (
        item.rule_id,
        item.experiment_id,
        item.category,
        item.severity,
        item.summary,
        item.evidence,
        item.recommended_action,
    )


def _validate_unique_items(
    items: Iterable[BriefItem],
    label: str,
) -> None:
    signatures = [_brief_item_signature(item) for item in items]

    if len(signatures) != len(set(signatures)):
        raise AgentGroundingError(f"The brief contains duplicate {label} findings.")


def validate_daily_brief(
    brief: OperationsBrief,
    analyses: list[ExperimentBlockerAnalysis],
    as_of: datetime,
) -> None:
    """Require the generated brief to match deterministic analysis exactly."""

    if brief.generated_at != as_of:
        raise AgentGroundingError("The brief uses an incorrect analysis timestamp.")

    if brief.experiments_reviewed != len(analyses):
        raise AgentGroundingError("The experiments-reviewed count is incorrect.")

    findings = [finding for analysis in analyses for finding in analysis.findings]

    expected_critical = {
        _finding_signature(finding) for finding in findings if finding.severity is Severity.CRITICAL
    }

    expected_warning = {
        _finding_signature(finding) for finding in findings if finding.severity is Severity.WARNING
    }

    _validate_unique_items(
        brief.critical_items,
        "critical",
    )
    _validate_unique_items(
        brief.warning_items,
        "warning",
    )

    actual_critical = {_brief_item_signature(item) for item in brief.critical_items}

    actual_warning = {_brief_item_signature(item) for item in brief.warning_items}

    if actual_critical != expected_critical:
        raise AgentGroundingError(
            "The brief's critical findings do not match deterministic analysis."
        )

    if actual_warning != expected_warning:
        raise AgentGroundingError(
            "The brief's warning findings do not match deterministic analysis."
        )

    expected_healthy_ids = {analysis.experiment_id for analysis in analyses if analysis.is_healthy}

    if set(brief.healthy_experiment_ids) != expected_healthy_ids:
        raise AgentGroundingError("The healthy experiment IDs do not match deterministic analysis.")

    recommended_actions = {finding.recommended_action for finding in findings}

    if findings:
        if brief.recommended_next_action not in recommended_actions:
            raise AgentGroundingError("The recommended next action is unsupported.")
    elif brief.recommended_next_action != "No action required.":
        raise AgentGroundingError("A healthy analysis must recommend no action.")
