from datetime import UTC, datetime
from pathlib import Path

import pytest

from labos_copilot.data import LabOSFixtures, load_labos_fixtures
from labos_copilot.domain import (
    Experiment,
    ExperimentStage,
    ExperimentStatus,
)
from labos_copilot.sdk import (
    DuplicateResourceError,
    ExperimentService,
    LabOSClient,
    ResourceNotFoundError,
)

FIXTURES_DIRECTORY = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def labos_client() -> LabOSClient:
    return LabOSClient.from_fixture_directory(FIXTURES_DIRECTORY)


def test_client_lists_active_experiments(
    labos_client: LabOSClient,
) -> None:
    experiments = labos_client.experiments.list_active()

    assert len(experiments) == 5
    assert all(
        experiment.status is ExperimentStatus.ACTIVE for experiment in experiments
    )


def test_client_gets_experiment_by_id(
    labos_client: LabOSClient,
) -> None:
    experiment = labos_client.experiments.get("EXP-103")

    assert experiment.name == "Expression validation batch C"
    assert experiment.current_stage is ExperimentStage.WAITING_FOR_MATERIALS


def test_client_gets_inventory_item(
    labos_client: LabOSClient,
) -> None:
    item = labos_client.inventory.get("MAT-002")

    assert item.quantity == 0
    assert item.name == "Expression reagent kit"


def test_client_gets_instrument(
    labos_client: LabOSClient,
) -> None:
    instrument = labos_client.instruments.get("INS-002")

    assert instrument.name == "Thermostability instrument 01"


def test_client_gets_deadline_for_experiment(
    labos_client: LabOSClient,
) -> None:
    deadline = labos_client.deadlines.get_for_experiment("EXP-105")

    assert deadline.customer_name == "Arcadia Pharma"
    assert deadline.id == "DL-105"


def test_unknown_experiment_raises_typed_error(
    labos_client: LabOSClient,
) -> None:
    with pytest.raises(
        ResourceNotFoundError,
        match="experiment resource not found: EXP-999",
    ):
        labos_client.experiments.get("EXP-999")


def test_unknown_inventory_item_raises_typed_error(
    labos_client: LabOSClient,
) -> None:
    with pytest.raises(
        ResourceNotFoundError,
        match="inventory item resource not found: MAT-999",
    ):
        labos_client.inventory.get("MAT-999")


def test_duplicate_experiment_ids_are_rejected() -> None:
    experiment = Experiment(
        id="EXP-DUPLICATE",
        name="Duplicate fixture",
        status=ExperimentStatus.ACTIVE,
        current_stage=ExperimentStage.QUEUED,
        stage_started_at=datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
        expected_stage_duration_hours=12,
    )

    with pytest.raises(
        DuplicateResourceError,
        match="Duplicate experiment resource",
    ):
        ExperimentService([experiment, experiment])


def test_client_can_be_built_from_loaded_fixtures() -> None:
    fixtures: LabOSFixtures = load_labos_fixtures(
        FIXTURES_DIRECTORY,
    )

    client = LabOSClient(fixtures)

    assert len(client.experiments.list_all()) == 5
    assert len(client.inventory.list_all()) == 3
    assert len(client.instruments.list_all()) == 3
    assert len(client.deadlines.list_all()) == 5
