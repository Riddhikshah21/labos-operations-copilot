"""Shared blocker-rule types."""

from collections.abc import Callable
from datetime import datetime

from labos_copilot.domain import BlockerFinding, Experiment
from labos_copilot.sdk import LabOSClient

BlockerRule = Callable[
    [Experiment, LabOSClient, datetime],
    list[BlockerFinding],
]
