"""Typed access to laboratory instruments."""

from collections.abc import Iterable

from labos_copilot.domain import Instrument
from labos_copilot.sdk.errors import (
    DuplicateResourceError,
    ResourceNotFoundError,
)


class InstrumentService:
    """Read-only access to laboratory instruments."""

    def __init__(self, instruments: Iterable[Instrument]) -> None:
        self._instruments_by_id: dict[str, Instrument] = {}

        for instrument in instruments:
            if instrument.id in self._instruments_by_id:
                raise DuplicateResourceError(
                    resource_type="instrument",
                    resource_id=instrument.id,
                )

            self._instruments_by_id[instrument.id] = instrument

    def list_all(self) -> list[Instrument]:
        """Return all instruments."""

        return list(self._instruments_by_id.values())

    def get(self, instrument_id: str) -> Instrument:
        """Return an instrument by identifier."""

        try:
            return self._instruments_by_id[instrument_id]
        except KeyError as exc:
            raise ResourceNotFoundError(
                resource_type="instrument",
                resource_id=instrument_id,
            ) from exc
