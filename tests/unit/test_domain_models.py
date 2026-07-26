from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from labos_copilot.domain import (
    Experiment,
    ExperimentStage,
    ExperimentStatus,
    InventoryItem,
    InventoryStatus,
)


def test_experiment_model_accepts_valid_data() -> None:
    experiment = Experiment(
        id="EXP-001",
        name="Test experiment",
        status=ExperimentStatus.ACTIVE,
        current_stage=ExperimentStage.RUNNING,
        stage_started_at=datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
        expected_stage_duration_hours=12,
        required_material_ids=["MAT-001"],
        required_instrument_id="INS-001",
        deadline_id="DL-001",
    )

    assert experiment.id == "EXP-001"
    assert experiment.status is ExperimentStatus.ACTIVE


def test_inventory_rejects_negative_quantity() -> None:
    with pytest.raises(ValidationError):
        InventoryItem(
            id="MAT-001",
            name="Invalid material",
            status=InventoryStatus.AVAILABLE,
            quantity=-1,
            minimum_required=1,
            unit="mL",
        )


def test_domain_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Experiment.model_validate(
            {
                "id": "EXP-001",
                "name": "Test experiment",
                "status": "active",
                "current_stage": "running",
                "stage_started_at": "2026-07-25T12:00:00Z",
                "expected_stage_duration_hours": 12,
                "required_material_ids": [],
                "required_instrument_id": None,
                "deadline_id": None,
                "unexpected_field": True,
            }
        )
