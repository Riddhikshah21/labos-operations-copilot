from datetime import UTC, datetime

import pytest

from labos_copilot.agent.schemas import (
    BriefItem,
    OperationsBrief,
)
from labos_copilot.domain import (
    BlockerCategory,
    Severity,
)
from labos_copilot.ui import (
    all_brief_items,
    find_brief_item,
    finding_counts,
    finding_key,
    finding_label,
)


def create_item(
    experiment_id: str,
    rule_id: str,
    severity: Severity,
) -> BriefItem:
    return BriefItem(
        rule_id=rule_id,
        experiment_id=experiment_id,
        category=BlockerCategory.DELAY,
        severity=severity,
        summary="Experiment stage is delayed.",
        evidence=("Elapsed duration exceeds limit.",),
        recommended_action="Request owner review.",
    )


def create_brief() -> OperationsBrief:
    return OperationsBrief(
        generated_at=datetime(
            2026,
            7,
            26,
            tzinfo=UTC,
        ),
        experiments_reviewed=3,
        executive_summary="Two findings detected.",
        critical_items=(
            create_item(
                "EXP-101",
                "stage-delay",
                Severity.CRITICAL,
            ),
        ),
        warning_items=(
            create_item(
                "EXP-102",
                "stage-delay",
                Severity.WARNING,
            ),
        ),
        healthy_experiment_ids=("EXP-103",),
        recommended_next_action=("Request owner review."),
    )


def test_combines_brief_items() -> None:
    brief = create_brief()

    items = all_brief_items(brief)

    assert len(items) == 2
    assert items[0].experiment_id == "EXP-101"
    assert items[1].experiment_id == "EXP-102"


def test_finding_key_and_label() -> None:
    item = create_item(
        "EXP-101",
        "stage-delay",
        Severity.CRITICAL,
    )

    assert finding_key(item) == "EXP-101|stage-delay"
    assert "EXP-101" in finding_label(item)
    assert "CRITICAL" in finding_label(item)


def test_finds_item_by_key() -> None:
    brief = create_brief()

    item = find_brief_item(
        brief,
        "EXP-102|stage-delay",
    )

    assert item.experiment_id == "EXP-102"


def test_unknown_item_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Unknown brief item",
    ):
        find_brief_item(
            create_brief(),
            "EXP-999|unknown",
        )


def test_counts_findings_by_severity() -> None:
    counts = finding_counts(create_brief())

    assert counts[Severity.CRITICAL] == 1
    assert counts[Severity.WARNING] == 1
