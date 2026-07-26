"""Customer deadline-risk detection."""

from datetime import datetime

from labos_copilot.domain import (
    BlockerCategory,
    BlockerFinding,
    Experiment,
    Severity,
)
from labos_copilot.sdk import LabOSClient, ResourceNotFoundError


def evaluate_deadline(
    experiment: Experiment,
    client: LabOSClient,
    as_of: datetime,
) -> list[BlockerFinding]:
    """Detect overdue or near-term customer deadlines."""

    deadline_id = experiment.deadline_id

    if deadline_id is None:
        return []

    try:
        deadline = client.deadlines.get(deadline_id)
    except ResourceNotFoundError:
        return [
            BlockerFinding(
                rule_id="missing-deadline-record",
                experiment_id=experiment.id,
                category=BlockerCategory.DEADLINE,
                severity=Severity.CRITICAL,
                summary="Associated deadline record is missing.",
                evidence=(
                    f"Expected deadline ID: {deadline_id}.",
                    "No matching deadline record was found.",
                ),
                recommended_action=(
                    "Verify the customer deadline with the commercial team."
                ),
            )
        ]

    if deadline.experiment_id != experiment.id:
        return [
            BlockerFinding(
                rule_id="deadline-experiment-mismatch",
                experiment_id=experiment.id,
                category=BlockerCategory.DEADLINE,
                severity=Severity.CRITICAL,
                summary="Deadline is linked to a different experiment.",
                evidence=(
                    f"Experiment ID: {experiment.id}.",
                    (f"Deadline {deadline.id} references {deadline.experiment_id}."),
                ),
                recommended_action="Correct the deadline association.",
            )
        ]

    if deadline.due_at.tzinfo is None or deadline.due_at.utcoffset() is None:
        raise ValueError("Deadline due_at must be timezone-aware.")

    remaining_hours = (deadline.due_at - as_of).total_seconds() / 3600

    if remaining_hours <= 0:
        severity = Severity.CRITICAL
        summary = "Customer deadline has passed."
    elif remaining_hours <= 24:
        severity = Severity.CRITICAL
        summary = "Customer deadline is less than 24 hours away."
    elif remaining_hours <= 72:
        severity = Severity.WARNING
        summary = "Customer deadline is less than 72 hours away."
    else:
        return []

    return [
        BlockerFinding(
            rule_id="deadline-risk",
            experiment_id=experiment.id,
            category=BlockerCategory.DEADLINE,
            severity=severity,
            summary=summary,
            evidence=(
                f"Customer: {deadline.customer_name}.",
                f"Deadline: {deadline.due_at.isoformat()}.",
                f"Remaining time: {remaining_hours:.1f} hours.",
                f"Priority: {deadline.priority.value}.",
            ),
            recommended_action=(
                "Review delivery risk and notify the experiment owner."
            ),
        )
    ]
