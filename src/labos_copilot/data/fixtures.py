"""Typed loading of mock LabOS fixture data."""

import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from labos_copilot.domain import (
    CustomerDeadline,
    Experiment,
    Instrument,
    InventoryItem,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class FixtureFormatError(ValueError):
    """Raised when fixture data is malformed or fails validation."""


class LabOSFixtures(BaseModel):
    """Complete collection of mock LabOS records."""

    experiments: list[Experiment]
    inventory: list[InventoryItem]
    instruments: list[Instrument]
    deadlines: list[CustomerDeadline]


def load_fixture_list(path: Path, model_type: type[ModelT]) -> list[ModelT]:
    """Load a JSON array and validate each item against a Pydantic model."""

    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FixtureFormatError(f"Fixture file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FixtureFormatError(f"Invalid JSON in fixture file: {path}") from exc

    if not isinstance(payload, list):
        raise FixtureFormatError(f"Fixture must contain a JSON array: {path}")

    validated_items: list[ModelT] = []

    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise FixtureFormatError(
                f"Fixture item {index} in {path} must be a JSON object."
            )

        try:
            validated_items.append(model_type.model_validate(item))
        except ValidationError as exc:
            raise FixtureFormatError(
                f"Fixture item {index} in {path} failed validation: {exc}"
            ) from exc

    return validated_items


def load_labos_fixtures(directory: Path) -> LabOSFixtures:
    """Load all mock LabOS datasets from a directory."""

    return LabOSFixtures(
        experiments=load_fixture_list(
            directory / "experiments.json",
            Experiment,
        ),
        inventory=load_fixture_list(
            directory / "inventory.json",
            InventoryItem,
        ),
        instruments=load_fixture_list(
            directory / "instruments.json",
            Instrument,
        ),
        deadlines=load_fixture_list(
            directory / "deadlines.json",
            CustomerDeadline,
        ),
    )
