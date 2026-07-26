"""Offline evaluation runner and Markdown reporting."""

import json
from datetime import UTC, datetime
from pathlib import Path

from labos_copilot.actions import ActionService
from labos_copilot.domain import (
    BlockerCategory,
    BlockerFinding,
    Severity,
)
from labos_copilot.evaluation.schemas import (
    ActionEvaluationCase,
    AnalysisEvaluationCase,
    EvaluationCaseResult,
    EvaluationSuite,
    EvaluationSummary,
    ExpectedFinding,
    LiveAgentEvaluationResult,
)
from labos_copilot.rules import BlockerEngine
from labos_copilot.sdk import LabOSClient

type FindingSignature = tuple[
    str,
    BlockerCategory,
    Severity,
]


def load_evaluation_suite(path: Path) -> EvaluationSuite:
    """Load and validate evaluation cases from JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return EvaluationSuite.model_validate(payload)


def _expected_signature(
    finding: ExpectedFinding,
) -> FindingSignature:
    return (
        finding.rule_id,
        finding.category,
        finding.severity,
    )


def _actual_signature(
    finding: BlockerFinding,
) -> FindingSignature:
    return (
        finding.rule_id,
        finding.category,
        finding.severity,
    )


def _signature_text(
    signature: FindingSignature,
) -> str:
    rule_id, category, severity = signature

    return f"{rule_id}:{category.value}:{severity.value}"


def evaluate_analysis_case(
    engine: BlockerEngine,
    case: AnalysisEvaluationCase,
) -> EvaluationCaseResult:
    """Evaluate one blocker-analysis scenario."""

    errors: list[str] = []
    observations: list[str] = []

    try:
        analysis = engine.analyze_experiment(
            case.experiment_id,
            case.as_of,
        )
    except Exception as exc:
        observed_error = type(exc).__name__

        if observed_error == case.expected_error_type:
            return EvaluationCaseResult(
                case_id=case.id,
                kind="analysis",
                passed=True,
                observations=(f"Observed expected error: {observed_error}",),
            )

        return EvaluationCaseResult(
            case_id=case.id,
            kind="analysis",
            passed=False,
            errors=(f"Unexpected {observed_error}: {exc}",),
        )

    if case.expected_error_type is not None:
        errors.append(f"Expected error {case.expected_error_type}, but analysis succeeded.")

    expected = {_expected_signature(finding) for finding in case.expected_findings}

    actual = {_actual_signature(finding) for finding in analysis.findings}

    matched = expected & actual
    missing = expected - actual
    unexpected = actual - expected

    if case.expected_healthy is not None and analysis.is_healthy != case.expected_healthy:
        errors.append(
            "Healthy classification mismatch: "
            f"expected={case.expected_healthy}, "
            f"actual={analysis.is_healthy}."
        )

    for signature in sorted(
        missing,
        key=_signature_text,
    ):
        errors.append(f"Missing finding: {_signature_text(signature)}")

    for signature in sorted(
        unexpected,
        key=_signature_text,
    ):
        errors.append(f"Unexpected finding: {_signature_text(signature)}")

    observations.extend(
        _signature_text(signature)
        for signature in sorted(
            actual,
            key=_signature_text,
        )
    )

    if not observations:
        observations.append("No blocker findings.")

    return EvaluationCaseResult(
        case_id=case.id,
        kind="analysis",
        passed=not errors,
        errors=tuple(errors),
        observations=tuple(observations),
        expected_findings=len(expected),
        actual_findings=len(actual),
        matched_findings=len(matched),
        missing_findings=len(missing),
        unexpected_findings=len(unexpected),
    )


def evaluate_action_case(
    engine: BlockerEngine,
    case: ActionEvaluationCase,
) -> EvaluationCaseResult:
    """Evaluate one mock-action scenario."""

    errors: list[str] = []

    service = ActionService(
        engine=engine,
        now_provider=lambda: case.as_of,
        id_factory=lambda: "ACT-EVALUATION",
    )

    try:
        action = service.prepare(
            experiment_id=case.experiment_id,
            rule_id=case.rule_id,
            as_of=case.as_of,
        )
    except Exception as exc:
        observed_error = type(exc).__name__

        if observed_error == case.expected_error_type:
            return EvaluationCaseResult(
                case_id=case.id,
                kind="action",
                passed=True,
                observations=(f"Observed expected error: {observed_error}",),
            )

        return EvaluationCaseResult(
            case_id=case.id,
            kind="action",
            passed=False,
            errors=(f"Unexpected {observed_error}: {exc}",),
        )

    if case.expected_error_type is not None:
        errors.append(
            f"Expected error {case.expected_error_type}, but action preparation succeeded."
        )

    if (
        case.expected_action_type is not None
        and action.action_type is not case.expected_action_type
    ):
        errors.append(
            "Action type mismatch: "
            f"expected={case.expected_action_type.value}, "
            f"actual={action.action_type.value}."
        )

    return EvaluationCaseResult(
        case_id=case.id,
        kind="action",
        passed=not errors,
        errors=tuple(errors),
        observations=(
            f"action_type={action.action_type.value}",
            f"status={action.status.value}",
        ),
    )


def run_evaluation_suite(
    suite: EvaluationSuite,
    fixture_directory: Path,
) -> EvaluationSummary:
    """Run every offline evaluation case."""

    client = LabOSClient.from_fixture_directory(fixture_directory)

    engine = BlockerEngine(client)

    results = [evaluate_analysis_case(engine, case) for case in suite.analysis_cases]

    results.extend(evaluate_action_case(engine, case) for case in suite.action_cases)

    total_cases = len(results)
    passed_cases = sum(result.passed for result in results)
    failed_cases = total_cases - passed_cases

    expected_findings = sum(result.expected_findings for result in results)

    matched_findings = sum(result.matched_findings for result in results)

    missing_findings = sum(result.missing_findings for result in results)

    unexpected_findings = sum(result.unexpected_findings for result in results)

    actual_findings = matched_findings + unexpected_findings

    precision = matched_findings / actual_findings if actual_findings else 1.0

    recall = matched_findings / expected_findings if expected_findings else 1.0

    pass_rate = passed_cases / total_cases if total_cases else 1.0

    return EvaluationSummary(
        generated_at=datetime.now(UTC),
        fixture_directory=str(fixture_directory),
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        pass_rate=pass_rate,
        expected_findings=expected_findings,
        matched_findings=matched_findings,
        missing_findings=missing_findings,
        unexpected_findings=unexpected_findings,
        finding_precision=precision,
        finding_recall=recall,
        results=tuple(results),
    )


def _percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def _escape_table_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_markdown_report(
    summary: EvaluationSummary,
    path: Path,
    live_results: tuple[
        LiveAgentEvaluationResult,
        ...,
    ] = (),
) -> None:
    """Write evaluation results to a Markdown report."""

    lines = [
        "# Evaluation Report",
        "",
        f"Generated: `{summary.generated_at.isoformat()}`",
        "",
        "## Offline Metrics",
        "",
        "| Metric | Result |",
        "|---|---:|",
        (
            f"| Case pass rate | "
            f"{summary.passed_cases}/{summary.total_cases} "
            f"({_percentage(summary.pass_rate)}) |"
        ),
        (f"| Finding precision | {_percentage(summary.finding_precision)} |"),
        (f"| Finding recall | {_percentage(summary.finding_recall)} |"),
        (f"| Missing findings | {summary.missing_findings} |"),
        (f"| Unexpected findings | {summary.unexpected_findings} |"),
        "",
        "## Offline Cases",
        "",
        "| Case | Type | Result | Details |",
        "|---|---|---|---|",
    ]

    for case_result in summary.results:
        status = "PASS" if case_result.passed else "FAIL"

        details = (
            "; ".join(case_result.errors)
            if case_result.errors
            else "; ".join(case_result.observations)
        )

        lines.append(
            f"| `{case_result.case_id}` | "
            f"{case_result.kind} | "
            f"**{status}** | "
            f"{_escape_table_text(details)} |"
        )

    if live_results:
        lines.extend(
            [
                "",
                "## Live Agent Cases",
                "",
                "| Case | Result | Tools | Details |",
                "|---|---|---|---|",
            ]
        )

        for live_result in live_results:
            status = "PASS" if live_result.passed else "FAIL"
            tools = ", ".join(live_result.tools_used)

            details = "; ".join(
                (
                    *live_result.errors,
                    *live_result.approval_decisions,
                )
            )

            lines.append(
                f"| `{live_result.case_id}` | "
                f"**{status}** | "
                f"{_escape_table_text(tools)} | "
                f"{_escape_table_text(details)} |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            ("Offline cases validate deterministic blocker classification and mock-action policy."),
            (
                "Live cases, when enabled, validate MCP tool "
                "selection and approval behavior using the configured LLM."
            ),
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
