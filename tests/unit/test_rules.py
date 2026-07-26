from datetime import UTC, datetime
from pathlib import Path

import pytest

from labos_copilot.domain import BlockerCategory, Severity
from labos_copilot.rules import BlockerEngine
from labos_copilot.sdk import LabOSClient

FIXTURES_DIRECTORY = Path(__file__).resolve().parents[2] / "fixtures"
ANALYSIS_TIME = datetime(2026, 7, 26, 0, 0, tzinfo=UTC)


@pytest.fixture
def engine() -> BlockerEngine:
    client = LabOSClient.from_fixture_directory(FIXTURES_DIRECTORY)
    return BlockerEngine(client)


def test_healthy_experiment_has_no_findings(
    engine: BlockerEngine,
) -> None:
    analysis = engine.analyze_experiment("EXP-101", ANALYSIS_TIME)

    assert analysis.is_healthy
    assert analysis.findings == ()


def test_delayed_experiment_is_detected(
    engine: BlockerEngine,
) -> None:
    analysis = engine.analyze_experiment("EXP-102", ANALYSIS_TIME)

    assert len(analysis.findings) == 1

    finding = analysis.findings[0]

    assert finding.category is BlockerCategory.DELAY
    assert finding.severity is Severity.CRITICAL


def test_out_of_stock_material_is_detected(
    engine: BlockerEngine,
) -> None:
    analysis = engine.analyze_experiment("EXP-103", ANALYSIS_TIME)

    assert len(analysis.findings) == 1

    finding = analysis.findings[0]

    assert finding.category is BlockerCategory.INVENTORY
    assert finding.severity is Severity.CRITICAL


def test_unavailable_instrument_is_detected(
    engine: BlockerEngine,
) -> None:
    analysis = engine.analyze_experiment("EXP-104", ANALYSIS_TIME)

    categories = {finding.category for finding in analysis.findings}

    assert categories == {BlockerCategory.INSTRUMENT}


def test_multiple_blockers_are_detected(
    engine: BlockerEngine,
) -> None:
    analysis = engine.analyze_experiment("EXP-105", ANALYSIS_TIME)

    findings_by_category = {finding.category: finding for finding in analysis.findings}

    assert set(findings_by_category) == {
        BlockerCategory.DELAY,
        BlockerCategory.INVENTORY,
        BlockerCategory.INSTRUMENT,
        BlockerCategory.DEADLINE,
    }

    assert findings_by_category[BlockerCategory.DEADLINE].severity is Severity.CRITICAL

    assert findings_by_category[BlockerCategory.INVENTORY].severity is Severity.WARNING


def test_all_active_experiments_are_analyzed(
    engine: BlockerEngine,
) -> None:
    analyses = engine.analyze_active(ANALYSIS_TIME)

    assert len(analyses) == 5
    assert sum(analysis.is_healthy for analysis in analyses) == 1


def test_naive_analysis_time_is_rejected(
    engine: BlockerEngine,
) -> None:
    naive_time = datetime(2026, 7, 26, 0, 0)  # noqa: DTZ001

    with pytest.raises(
        ValueError,
        match="Analysis time must be timezone-aware",
    ):
        engine.analyze_active(naive_time)
