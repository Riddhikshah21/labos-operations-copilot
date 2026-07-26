from datetime import UTC, datetime
from pathlib import Path

import pytest

from labos_copilot.actions import (
    ActionPreparationError,
    ActionService,
)
from labos_copilot.domain import (
    ActionStatus,
    ActionType,
)
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


@pytest.fixture
def action_service() -> ActionService:
    client = LabOSClient.from_fixture_directory(FIXTURES_DIRECTORY)

    return ActionService(
        engine=BlockerEngine(client),
        now_provider=lambda: ANALYSIS_TIME,
        id_factory=lambda: "ACT-TEST",
    )


def test_prepares_action_from_existing_finding(
    action_service: ActionService,
) -> None:
    action = action_service.prepare(
        experiment_id="EXP-105",
        rule_id="deadline-risk",
    )

    assert action.id == "ACT-TEST"
    assert action.experiment_id == "EXP-105"
    assert action.action_type is ActionType.ESCALATE_DELIVERY_RISK
    assert action.status is ActionStatus.MOCK_COMPLETED
    assert action.created_at == ANALYSIS_TIME


def test_inventory_finding_maps_to_procurement(
    action_service: ActionService,
) -> None:
    action = action_service.prepare(
        experiment_id="EXP-103",
        rule_id="inventory-out-of-stock",
    )

    assert action.action_type is ActionType.ESCALATE_MATERIAL_PROCUREMENT


def test_unknown_finding_is_rejected(
    action_service: ActionService,
) -> None:
    with pytest.raises(
        ActionPreparationError,
        match="No finding",
    ):
        action_service.prepare(
            experiment_id="EXP-105",
            rule_id="unknown-rule",
        )
