"""Command-line entry point for project evaluations."""

import argparse
import asyncio
from datetime import UTC, datetime
from pathlib import Path

from labos_copilot.agent.service import (
    run_daily_operations_agent,
)
from labos_copilot.config import Settings
from labos_copilot.evaluation.runner import (
    load_evaluation_suite,
    run_evaluation_suite,
    write_markdown_report,
)
from labos_copilot.evaluation.schemas import (
    LiveAgentEvaluationResult,
)


async def run_live_agent_evaluations(
    settings: Settings,
) -> tuple[LiveAgentEvaluationResult, ...]:
    """Run optional real-LLM workflow evaluations."""

    analysis_time = datetime(
        2026,
        7,
        26,
        0,
        0,
        tzinfo=UTC,
    )

    results: list[LiveAgentEvaluationResult] = []

    try:
        review = await run_daily_operations_agent(
            question=("Which experiments need attention today?"),
            settings=settings,
            as_of=analysis_time,
        )

        errors: list[str] = []

        if not any(tool.endswith("analyze_active_experiments") for tool in review.tools_used):
            errors.append("Required analysis tool was not used.")

        if review.approval_decisions:
            errors.append("Review-only request unexpectedly required approval.")

        if review.brief.experiments_reviewed != 5:
            errors.append("The agent did not report five reviewed experiments.")

        results.append(
            LiveAgentEvaluationResult(
                case_id="live-daily-review",
                passed=not errors,
                errors=tuple(errors),
                tools_used=review.tools_used,
            )
        )

    except Exception as exc:
        results.append(
            LiveAgentEvaluationResult(
                case_id="live-daily-review",
                passed=False,
                errors=(f"{type(exc).__name__}: {exc}",),
            )
        )

    async def reject_action(
        _tool_name: str,
        _arguments: str | None,
    ) -> bool:
        return False

    try:
        action_run = await run_daily_operations_agent(
            question=("Review today's experiments and prepare the highest-priority mock action."),
            settings=settings,
            as_of=analysis_time,
            approval_callback=reject_action,
        )

        errors = []

        if not any(tool.endswith("prepare_operations_action") for tool in action_run.tools_used):
            errors.append("The action tool was not requested.")

        rejected = any(not decision.approved for decision in action_run.approval_decisions)

        if not rejected:
            errors.append("The rejected approval was not recorded.")

        decisions = tuple(
            (f"{decision.tool_name}={'approved' if decision.approved else 'rejected'}")
            for decision in action_run.approval_decisions
        )

        results.append(
            LiveAgentEvaluationResult(
                case_id="live-action-rejection",
                passed=not errors,
                errors=tuple(errors),
                tools_used=action_run.tools_used,
                approval_decisions=decisions,
            )
        )

    except Exception as exc:
        results.append(
            LiveAgentEvaluationResult(
                case_id="live-action-rejection",
                passed=False,
                errors=(f"{type(exc).__name__}: {exc}",),
            )
        )

    return tuple(results)


def main() -> None:
    """Run evaluations and generate the report."""

    parser = argparse.ArgumentParser(
        description="Evaluate LabOS Operations Copilot.",
    )

    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("evaluations/cases.json"),
    )

    parser.add_argument(
        "--report",
        type=Path,
        default=Path("evaluations/report.md"),
    )

    parser.add_argument(
        "--live-agent",
        action="store_true",
        help="Run two real LLM evaluations.",
    )

    arguments = parser.parse_args()
    settings = Settings()

    suite = load_evaluation_suite(arguments.cases)

    summary = run_evaluation_suite(
        suite=suite,
        fixture_directory=(settings.labos_fixtures_dir.resolve()),
    )

    live_results: tuple[
        LiveAgentEvaluationResult,
        ...,
    ] = ()

    if arguments.live_agent:
        live_results = asyncio.run(run_live_agent_evaluations(settings))

    write_markdown_report(
        summary=summary,
        path=arguments.report,
        live_results=live_results,
    )

    print(f"Offline cases: {summary.passed_cases}/{summary.total_cases} passed")

    print(f"Finding precision: {summary.finding_precision:.1%}")

    print(f"Finding recall: {summary.finding_recall:.1%}")

    print(f"Report: {arguments.report}")

    live_failed = any(not result.passed for result in live_results)

    if summary.failed_cases or live_failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
