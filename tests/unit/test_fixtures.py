from pathlib import Path

import pytest

from labos_copilot.data import FixtureFormatError, load_labos_fixtures

FIXTURES_DIRECTORY = Path(__file__).resolve().parents[2] / "fixtures"


def test_load_all_labos_fixtures() -> None:
    fixtures = load_labos_fixtures(FIXTURES_DIRECTORY)

    assert len(fixtures.experiments) == 5
    assert len(fixtures.inventory) == 3
    assert len(fixtures.instruments) == 3
    assert len(fixtures.deadlines) == 5


def test_expected_experiment_scenarios_exist() -> None:
    fixtures = load_labos_fixtures(FIXTURES_DIRECTORY)

    experiment_ids = {experiment.id for experiment in fixtures.experiments}

    assert experiment_ids == {
        "EXP-101",
        "EXP-102",
        "EXP-103",
        "EXP-104",
        "EXP-105",
    }


def test_missing_fixture_directory_raises_clear_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(FixtureFormatError, match="Fixture file not found"):
        load_labos_fixtures(tmp_path)
