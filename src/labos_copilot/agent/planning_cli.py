"""CLI for AI-generated operational action plans."""

import argparse
import asyncio
from datetime import datetime

from labos_copilot.agent.planning import (
    run_action_planning_agent,
)
from labos_copilot.config import Settings


def parse_timestamp(value: str) -> datetime:
    """Parse a timezone-aware ISO timestamp."""

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("Timestamp must include a timezone.")

    return parsed


async def run(
    experiment_id: str,
    rule_id: str,
    as_of: datetime | None,
) -> None:
    """Run and display one planning workflow."""

    result = await run_action_planning_agent(
        experiment_id=experiment_id,
        rule_id=rule_id,
        settings=Settings(),
        as_of=as_of,
    )

    print(result.plan.model_dump_json(indent=2))

    print("\nTools used:")

    for tool_name in result.tools_used:
        print(f"- {tool_name}")


def main() -> None:
    """Run the planning CLI."""

    parser = argparse.ArgumentParser(description="Generate grounded operational action plans.")

    parser.add_argument("experiment_id")
    parser.add_argument("rule_id")

    parser.add_argument(
        "--as-of",
        type=parse_timestamp,
        default=None,
    )

    arguments = parser.parse_args()

    asyncio.run(
        run(
            experiment_id=arguments.experiment_id,
            rule_id=arguments.rule_id,
            as_of=arguments.as_of,
        )
    )


if __name__ == "__main__":
    main()
