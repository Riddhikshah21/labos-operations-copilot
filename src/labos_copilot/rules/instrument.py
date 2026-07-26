"""Instrument availability blocker detection."""

from datetime import datetime

from labos_copilot.domain import (
    BlockerCategory,
    BlockerFinding,
    Experiment,
    InstrumentStatus,
    Severity,
)
from labos_copilot.sdk import LabOSClient, ResourceNotFoundError


def evaluate_instrument(
    experiment: Experiment,
    client: LabOSClient,
    _as_of: datetime,
) -> list[BlockerFinding]:
    """Detect unavailable required instruments."""

    instrument_id = experiment.required_instrument_id

    if instrument_id is None:
        return []

    try:
        instrument = client.instruments.get(instrument_id)
    except ResourceNotFoundError:
        return [
            BlockerFinding(
                rule_id="missing-instrument-record",
                experiment_id=experiment.id,
                category=BlockerCategory.INSTRUMENT,
                severity=Severity.CRITICAL,
                summary="Required instrument record is missing.",
                evidence=(
                    f"Required instrument ID: {instrument_id}.",
                    "No matching instrument record was found.",
                ),
                recommended_action=(
                    "Verify the instrument identifier and contact lab operations."
                ),
            )
        ]

    if instrument.status is InstrumentStatus.AVAILABLE:
        return []

    if instrument.status is InstrumentStatus.BUSY:
        availability = (
            instrument.available_at.isoformat()
            if instrument.available_at is not None
            else "unknown"
        )

        return [
            BlockerFinding(
                rule_id="instrument-busy",
                experiment_id=experiment.id,
                category=BlockerCategory.INSTRUMENT,
                severity=Severity.WARNING,
                summary="Required instrument is currently busy.",
                evidence=(
                    f"Instrument: {instrument.id} — {instrument.name}.",
                    f"Instrument status: {instrument.status.value}.",
                    f"Expected availability: {availability}.",
                ),
                recommended_action=(
                    "Review the instrument schedule or assign another instrument."
                ),
            )
        ]

    return [
        BlockerFinding(
            rule_id=f"instrument-{instrument.status.value}",
            experiment_id=experiment.id,
            category=BlockerCategory.INSTRUMENT,
            severity=Severity.CRITICAL,
            summary="Required instrument is unavailable.",
            evidence=(
                f"Instrument: {instrument.id} — {instrument.name}.",
                f"Instrument status: {instrument.status.value}.",
            ),
            recommended_action=(
                "Contact lab operations and reschedule or assign another instrument."
            ),
        )
    ]
