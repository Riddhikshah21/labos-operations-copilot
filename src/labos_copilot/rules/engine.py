"""Deterministic blocker-analysis engine."""

from collections.abc import Iterable
from datetime import datetime

from labos_copilot.domain import (
    ExperimentBlockerAnalysis,
    Severity,
)
from labos_copilot.rules.base import BlockerRule
from labos_copilot.rules.deadline import evaluate_deadline
from labos_copilot.rules.delay import evaluate_delay
from labos_copilot.rules.instrument import evaluate_instrument
from labos_copilot.rules.inventory import evaluate_inventory
from labos_copilot.sdk import LabOSClient

DEFAULT_RULES: tuple[BlockerRule, ...] = (
    evaluate_delay,
    evaluate_inventory,
    evaluate_instrument,
    evaluate_deadline,
)

_SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.WARNING: 1,
    Severity.INFO: 2,
}


class BlockerEngine:
    """Run deterministic operational rules against LabOS data."""

    def __init__(
        self,
        client: LabOSClient,
        rules: Iterable[BlockerRule] | None = None,
    ) -> None:
        self._client = client
        self._rules = tuple(rules) if rules is not None else DEFAULT_RULES

    def analyze_experiment(
        self,
        experiment_id: str,
        as_of: datetime,
    ) -> ExperimentBlockerAnalysis:
        """Analyze one experiment."""

        self._validate_analysis_time(as_of)

        experiment = self._client.experiments.get(experiment_id)
        findings = []

        for rule in self._rules:
            findings.extend(rule(experiment, self._client, as_of))

        findings.sort(
            key=lambda finding: (
                _SEVERITY_ORDER[finding.severity],
                finding.category.value,
                finding.rule_id,
            )
        )

        return ExperimentBlockerAnalysis(
            experiment_id=experiment.id,
            findings=tuple(findings),
        )

    def analyze_active(
        self,
        as_of: datetime,
    ) -> list[ExperimentBlockerAnalysis]:
        """Analyze every active experiment."""

        self._validate_analysis_time(as_of)

        return [
            self.analyze_experiment(experiment.id, as_of)
            for experiment in self._client.experiments.list_active()
        ]

    @staticmethod
    def _validate_analysis_time(as_of: datetime) -> None:
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("Analysis time must be timezone-aware.")
