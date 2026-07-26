"""Presentation helpers for the Streamlit interface."""

from labos_copilot.agent.schemas import BriefItem, OperationsBrief
from labos_copilot.domain import Severity


def all_brief_items(
    brief: OperationsBrief,
) -> tuple[BriefItem, ...]:
    """Return critical and warning findings in display order."""

    return (
        *brief.critical_items,
        *brief.warning_items,
    )


def finding_key(item: BriefItem) -> str:
    """Create a stable UI key for a brief item."""

    return f"{item.experiment_id}|{item.rule_id}"


def finding_label(item: BriefItem) -> str:
    """Create a concise human-readable finding label."""

    return (
        f"{item.experiment_id} · "
        f"{item.severity.value.upper()} · "
        f"{item.category.value} · "
        f"{item.rule_id}"
    )


def find_brief_item(
    brief: OperationsBrief,
    key: str,
) -> BriefItem:
    """Find one brief item by its stable key."""

    for item in all_brief_items(brief):
        if finding_key(item) == key:
            return item

    raise ValueError(f"Unknown brief item: {key}")


def finding_counts(
    brief: OperationsBrief,
) -> dict[Severity, int]:
    """Return finding counts grouped by severity."""

    return {
        Severity.CRITICAL: len(brief.critical_items),
        Severity.WARNING: len(brief.warning_items),
    }
