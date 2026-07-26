"""Command-line interface for the LabOS agent."""

import argparse
import asyncio

from labos_copilot.agent.service import (
    run_daily_operations_agent,
)
from labos_copilot.config import Settings


def prompt_approval_sync(
    tool_name: str,
    arguments: str | None,
) -> bool:
    """Collect a human approval decision from the terminal."""

    print("\nApproval required")
    print(f"Tool: {tool_name}")
    print(f"Arguments: {arguments}")

    response = input("Approve this simulated action? [y/N]: ").strip().lower()

    return response in {"y", "yes"}


async def prompt_approval(
    tool_name: str,
    arguments: str | None,
) -> bool:
    """Run the blocking terminal prompt outside the event loop."""

    return await asyncio.to_thread(
        prompt_approval_sync,
        tool_name,
        arguments,
    )


async def run(question: str) -> None:
    """Execute and print one agent run."""

    result = await run_daily_operations_agent(
        question=question,
        settings=Settings(),
        approval_callback=prompt_approval,
    )

    print(result.brief.model_dump_json(indent=2))

    print("\nTools used:")

    for tool_name in result.tools_used:
        print(f"- {tool_name}")

    if result.approval_decisions:
        print("\nApproval decisions:")

        for decision in result.approval_decisions:
            status = "approved" if decision.approved else "rejected"

            print(f"- {decision.tool_name}: {status}")


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
