"""Experiment-stage delay detection."""

from datetime import datetime

from labos_copilot.domain import (
    BlockerCategory,
    BlockerFinding,
    Experiment,
    Severity,
)
from labos_copilot.sdk import LabOSClient


def evaluate_delay(
    experiment: Experiment,
    _client: LabOSClient,
    as_of: datetime,
) -> list[BlockerFinding]:
    """Detect whether an experiment stage exceeds its expected duration."""

    stage_started_at = experiment.stage_started_at

    if stage_started_at.tzinfo is None or stage_started_at.utcoffset() is None:
        raise ValueError("Experiment stage_started_at must be timezone-aware.")

    elapsed_hours = (as_of - stage_started_at).total_seconds() / 3600

    if elapsed_hours < 0:
        raise ValueError(f"Experiment {experiment.id} starts after the analysis time.")

    expected_hours = experiment.expected_stage_duration_hours

    if elapsed_hours <= expected_hours:
        return []

    overrun_ratio = elapsed_hours / expected_hours
    severity = Severity.CRITICAL if overrun_ratio >= 2 else Severity.WARNING

    return [
        BlockerFinding(
            rule_id="stage-delay",
            experiment_id=experiment.id,
            category=BlockerCategory.DELAY,
            severity=severity,
            summary="Current experiment stage exceeds its expected duration.",
            evidence=(
                f"Current stage: {experiment.current_stage.value}.",
                f"Elapsed stage time: {elapsed_hours:.1f} hours.",
                f"Expected stage duration: {expected_hours:.1f} hours.",
            ),
            recommended_action=(
                "Ask the experiment owner to review the stage status "
                "and determine whether intervention is required."
            ),
        )
    ]
