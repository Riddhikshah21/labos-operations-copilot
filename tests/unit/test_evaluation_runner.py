from pathlib import Path

from labos_copilot.evaluation import (
    load_evaluation_suite,
    run_evaluation_suite,
    write_markdown_report,
)

PROJECT_DIRECTORY = Path(__file__).resolve().parents[2]
FIXTURES_DIRECTORY = PROJECT_DIRECTORY / "fixtures"
CASES_PATH = PROJECT_DIRECTORY / "evaluations/cases.json"


def test_offline_evaluation_suite_passes() -> None:
    suite = load_evaluation_suite(CASES_PATH)

    summary = run_evaluation_suite(
        suite,
        FIXTURES_DIRECTORY,
    )

    assert summary.total_cases == 9
    assert summary.passed_cases == 9
    assert summary.failed_cases == 0
    assert summary.finding_precision == 1.0
    assert summary.finding_recall == 1.0


def test_evaluation_report_is_written(
    tmp_path: Path,
) -> None:
    suite = load_evaluation_suite(CASES_PATH)

    summary = run_evaluation_suite(
        suite,
        FIXTURES_DIRECTORY,
    )

    report_path = tmp_path / "report.md"

    write_markdown_report(
        summary,
        report_path,
    )

    report = report_path.read_text(encoding="utf-8")

    assert "# Evaluation Report" in report
    assert "100.0%" in report
    assert "multiple-blockers" in report


def test_incorrect_expectation_fails() -> None:
    suite = load_evaluation_suite(CASES_PATH)

    first_case = suite.analysis_cases[0]

    invalid_case = first_case.model_copy(
        update={
            "expected_healthy": False,
        }
    )

    invalid_suite = suite.model_copy(
        update={
            "analysis_cases": (
                invalid_case,
                *suite.analysis_cases[1:],
            )
        }
    )

    summary = run_evaluation_suite(
        invalid_suite,
        FIXTURES_DIRECTORY,
    )

    assert summary.failed_cases == 1
