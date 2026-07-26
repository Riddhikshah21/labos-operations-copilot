"""Unified typed client for mock LabOS services."""

from pathlib import Path

from labos_copilot.data import LabOSFixtures, load_labos_fixtures
from labos_copilot.sdk.deadlines import DeadlineService
from labos_copilot.sdk.experiments import ExperimentService
from labos_copilot.sdk.instruments import InstrumentService
from labos_copilot.sdk.inventory import InventoryService


class LabOSClient:
    """Entry point for typed access to LabOS capabilities."""

    def __init__(self, fixtures: LabOSFixtures) -> None:
        self.experiments = ExperimentService(fixtures.experiments)
        self.inventory = InventoryService(fixtures.inventory)
        self.instruments = InstrumentService(fixtures.instruments)
        self.deadlines = DeadlineService(fixtures.deadlines)

    @classmethod
    def from_fixture_directory(cls, directory: Path) -> "LabOSClient":
        """Construct a client from validated JSON fixture files."""

        fixtures = load_labos_fixtures(directory)
        return cls(fixtures)
