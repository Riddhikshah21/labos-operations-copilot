from datetime import UTC, datetime
from pathlib import Path

import pytest

from labos_copilot.agent.errors import (
    AgentGroundingError,
)
from labos_copilot.agent.grounding import (
    validate_daily_brief,
)
from labos_copilot.agent.schemas import (
    BriefItem,
    OperationsBrief,
)
from labos_copilot.domain import ExperimentBlockerAnalysis, Severity
from labos_copilot.rules import BlockerEngine
from labos_copilot.sdk import LabOSClient

FIXTURES_DIRECTORY = Path(__file__).resolve().parents[2] / "fixtures"

ANALYSIS_TIME = datetime(
    2026,
    7,
    26,
    0,
    0,
    tzinfo=UTC,
)


def create_grounded_brief() -> tuple[
    OperationsBrief,
    list[ExperimentBlockerAnalysis],
]:
    client = LabOSClient.from_fixture_directory(FIXTURES_DIRECTORY)

    analyses = BlockerEngine(client).analyze_active(ANALYSIS_TIME)

    findings = [finding for analysis in analyses for finding in analysis.findings]

    critical_items = tuple(
        BriefItem(
            rule_id=finding.rule_id,
            experiment_id=finding.experiment_id,
            category=finding.category,
            severity=finding.severity,
            summary=finding.summary,
            evidence=finding.evidence,
            recommended_action=(finding.recommended_action),
        )
        for finding in findings
        if finding.severity is Severity.CRITICAL
    )

    warning_items = tuple(
        BriefItem(
            rule_id=finding.rule_id,
            experiment_id=finding.experiment_id,
            category=finding.category,
            severity=finding.severity,
            summary=finding.summary,
            evidence=finding.evidence,
            recommended_action=(finding.recommended_action),
        )
        for finding in findings
        if finding.severity is Severity.WARNING
    )

    healthy_ids = tuple(analysis.experiment_id for analysis in analyses if analysis.is_healthy)

    brief = OperationsBrief(
        generated_at=ANALYSIS_TIME,
        experiments_reviewed=len(analyses),
        executive_summary=("Several experiments require attention."),
        critical_items=critical_items,
        warning_items=warning_items,
        healthy_experiment_ids=healthy_ids,
        recommended_next_action=(critical_items[0].recommended_action),
    )

    return brief, analyses


def test_grounded_brief_is_accepted() -> None:
    brief, analyses = create_grounded_brief()

    validate_daily_brief(
        brief,
        analyses,
        ANALYSIS_TIME,
    )


def test_invented_evidence_is_rejected() -> None:
    brief, analyses = create_grounded_brief()

    first_item = brief.critical_items[0]

    invalid_item = first_item.model_copy(
        update={
            "evidence": ("Invented evidence.",),
        }
    )

    invalid_brief = brief.model_copy(
        update={
            "critical_items": (
                invalid_item,
                *brief.critical_items[1:],
            )
        }
    )

    with pytest.raises(
        AgentGroundingError,
        match="critical findings",
    ):
        validate_daily_brief(
            invalid_brief,
            analyses,
            ANALYSIS_TIME,
        )


def test_unsupported_healthy_id_is_rejected() -> None:
    brief, analyses = create_grounded_brief()

    invalid_brief = brief.model_copy(
        update={
            "healthy_experiment_ids": (
                *brief.healthy_experiment_ids,
                "EXP-999",
            )
        }
    )

    with pytest.raises(
        AgentGroundingError,
        match="healthy experiment IDs",
    ):
        validate_daily_brief(
            invalid_brief,
            analyses,
            ANALYSIS_TIME,
        )
