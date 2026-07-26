"""Command-line interface for the LabOS agent."""

import argparse
import asyncio

from labos_copilot.agent.service import (
    run_daily_operations_agent,
)
from labos_copilot.config import Settings


async def run(question: str) -> None:
    """Execute and print one agent run."""

    result = await run_daily_operations_agent(
        question=question,
        settings=Settings(),
    )

    print(result.brief.model_dump_json(indent=2))

    print("\nTools used:")

    for tool_name in result.tools_used:
        print(f"- {tool_name}")


def main() -> None:
    """Run the command-line application."""

    parser = argparse.ArgumentParser(
        description="Run LabOS Operations Copilot.",
    )

    parser.add_argument(
        "question",
        nargs="?",
        default=("Which experiments need attention today?"),
    )

    arguments = parser.parse_args()

    asyncio.run(run(arguments.question))


if __name__ == "__main__":
    main()
