"""Inventory blocker detection."""

from datetime import datetime

from labos_copilot.domain import (
    BlockerCategory,
    BlockerFinding,
    Experiment,
    InventoryStatus,
    Severity,
)
from labos_copilot.sdk import LabOSClient, ResourceNotFoundError


def evaluate_inventory(
    experiment: Experiment,
    client: LabOSClient,
    _as_of: datetime,
) -> list[BlockerFinding]:
    """Detect unavailable or insufficient required materials."""

    findings: list[BlockerFinding] = []

    for material_id in experiment.required_material_ids:
        try:
            item = client.inventory.get(material_id)
        except ResourceNotFoundError:
            findings.append(
                BlockerFinding(
                    rule_id="missing-inventory-record",
                    experiment_id=experiment.id,
                    category=BlockerCategory.INVENTORY,
                    severity=Severity.CRITICAL,
                    summary="Required inventory record is missing.",
                    evidence=(
                        f"Required material ID: {material_id}.",
                        "No matching inventory record was found.",
                    ),
                    recommended_action=(
                        "Verify the material identifier and contact lab operations."
                    ),
                )
            )
            continue

        if item.status is InventoryStatus.OUT_OF_STOCK or item.quantity <= 0:
            findings.append(
                BlockerFinding(
                    rule_id="inventory-out-of-stock",
                    experiment_id=experiment.id,
                    category=BlockerCategory.INVENTORY,
                    severity=Severity.CRITICAL,
                    summary="Required material is out of stock.",
                    evidence=(
                        f"Material: {item.id} — {item.name}.",
                        f"Available quantity: {item.quantity:g} {item.unit}.",
                        f"Inventory status: {item.status.value}.",
                    ),
                    recommended_action=(
                        "Escalate material procurement or identify an approved substitute."
                    ),
                )
            )
            continue

        if item.status is InventoryStatus.LOW_STOCK or item.quantity < item.minimum_required:
            findings.append(
                BlockerFinding(
                    rule_id="inventory-below-minimum",
                    experiment_id=experiment.id,
                    category=BlockerCategory.INVENTORY,
                    severity=Severity.WARNING,
                    summary="Required material is below the minimum quantity.",
                    evidence=(
                        f"Material: {item.id} — {item.name}.",
                        f"Available quantity: {item.quantity:g} {item.unit}.",
                        (f"Minimum required quantity: {item.minimum_required:g} {item.unit}."),
                    ),
                    recommended_action=(
                        "Confirm sufficient material is reserved before proceeding."
                    ),
                )
            )

    return findings
