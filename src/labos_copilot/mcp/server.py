"""MCP server exposing LabOS operational capabilities."""

from __future__ import annotations
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from labos_copilot.mcp.tools import (
    LabOSToolService,
    NowProvider,
    utc_now,
)
from labos_copilot.sdk import LabOSClient


def serialize_model(model: BaseModel) -> dict[str, Any]:
    """Convert a Pydantic model into a JSON-compatible dictionary."""

    return model.model_dump(mode="json")


def create_mcp_server(
    fixture_directory: Path,
    now_provider: NowProvider = utc_now,
) -> FastMCP:
    """Create and configure the LabOS MCP server."""

    client = LabOSClient.from_fixture_directory(fixture_directory)
    tools = LabOSToolService(
        client=client,
        now_provider=now_provider,
    )

    server = FastMCP(
        "LabOS Operations Copilot",
        json_response=True,
    )

    @server.tool()
    def list_active_experiments() -> dict[str, Any]:
        """List active laboratory experiments and their current stages."""

        return serialize_model(tools.list_active_experiments())

    @server.tool()
    def get_experiment_details(
        experiment_id: str,
    ) -> dict[str, Any]:
        """Get an experiment and its inventory, instrument, and deadline context."""

        return serialize_model(
            tools.get_experiment_details(experiment_id),
        )

    @server.tool()
    def get_inventory_status(
        material_id: str,
    ) -> dict[str, Any]:
        """Get the availability and quantity of one laboratory material."""

        return serialize_model(
            tools.get_inventory_status(material_id),
        )

    @server.tool()
    def get_instrument_status(
        instrument_id: str,
    ) -> dict[str, Any]:
        """Get the operational status of one laboratory instrument."""

        return serialize_model(
            tools.get_instrument_status(instrument_id),
        )

    @server.tool()
    def get_customer_deadline(
        experiment_id: str,
    ) -> dict[str, Any]:
        """Get the customer deadline associated with an experiment."""

        return serialize_model(
            tools.get_customer_deadline(experiment_id),
        )

    @server.tool()
    def analyze_experiment_blockers(
        experiment_id: str,
        as_of: datetime | None = None,
    ) -> dict[str, Any]:
        """Analyze one experiment for deterministic operational blockers."""

        return serialize_model(
            tools.analyze_experiment_blockers(
                experiment_id=experiment_id,
                as_of=as_of,
            )
        )

    @server.tool()
    def analyze_active_experiments(
        as_of: datetime | None = None,
    ) -> dict[str, Any]:
        """Analyze every active experiment for operational blockers."""

        return serialize_model(
            tools.analyze_active_experiments(as_of),
        )

    return server


def default_fixture_directory() -> Path:
    """Resolve the fixture directory from configuration or repository layout."""

    configured_directory = os.getenv("LABOS_FIXTURES_DIR")

    if configured_directory:
        return Path(configured_directory)

    return Path(__file__).resolve().parents[3] / "fixtures"


mcp = create_mcp_server(default_fixture_directory())

def main() -> None:
    """Run the MCP server over standard input and output."""

    print(
        "LabOS MCP server running over stdio.",
        file=sys.stderr,
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
