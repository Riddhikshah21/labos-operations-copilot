from datetime import UTC, datetime
from pathlib import Path

import pytest
from mcp.server.fastmcp import FastMCP

from labos_copilot.domain import BlockerCategory
from labos_copilot.mcp.server import create_mcp_server
from labos_copilot.mcp.tools import LabOSToolService
from labos_copilot.sdk import (
    LabOSClient,
    ResourceNotFoundError,
)

FIXTURES_DIRECTORY = Path(__file__).resolve().parents[2] / "fixtures"
ANALYSIS_TIME = datetime(2026, 7, 26, 0, 0, tzinfo=UTC)


@pytest.fixture
def tool_service() -> LabOSToolService:
    client = LabOSClient.from_fixture_directory(FIXTURES_DIRECTORY)

    return LabOSToolService(
        client=client,
        now_provider=lambda: ANALYSIS_TIME,
    )


def test_lists_active_experiments(
    tool_service: LabOSToolService,
) -> None:
    response = tool_service.list_active_experiments()

    assert response.count == 5
    assert response.experiments[0].id == "EXP-101"


def test_gets_complete_experiment_context(
    tool_service: LabOSToolService,
) -> None:
    context = tool_service.get_experiment_details("EXP-105")

    assert context.experiment.id == "EXP-105"
    assert context.inventory[0].id == "MAT-003"
    assert context.instrument is not None
    assert context.instrument.id == "INS-003"
    assert context.deadline is not None
    assert context.deadline.id == "DL-105"


def test_gets_inventory_status(
    tool_service: LabOSToolService,
) -> None:
    item = tool_service.get_inventory_status("MAT-002")

    assert item.quantity == 0


def test_analyzes_experiment_blockers(
    tool_service: LabOSToolService,
) -> None:
    analysis = tool_service.analyze_experiment_blockers("EXP-105")

    categories = {finding.category for finding in analysis.findings}

    assert categories == {
        BlockerCategory.DELAY,
        BlockerCategory.INVENTORY,
        BlockerCategory.INSTRUMENT,
        BlockerCategory.DEADLINE,
    }


def test_analyzes_all_active_experiments(
    tool_service: LabOSToolService,
) -> None:
    response = tool_service.analyze_active_experiments()

    assert response.as_of == ANALYSIS_TIME
    assert len(response.analyses) == 5
    assert sum(analysis.is_healthy for analysis in response.analyses) == 1


def test_unknown_experiment_raises_typed_error(
    tool_service: LabOSToolService,
) -> None:
    with pytest.raises(ResourceNotFoundError):
        tool_service.get_experiment_details("EXP-999")


def test_mcp_server_can_be_created() -> None:
    server = create_mcp_server(FIXTURES_DIRECTORY)

    assert isinstance(server, FastMCP)
