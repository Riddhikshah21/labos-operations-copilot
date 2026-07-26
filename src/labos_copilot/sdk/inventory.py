"""Typed access to laboratory inventory."""

from collections.abc import Iterable

from labos_copilot.domain import InventoryItem
from labos_copilot.sdk.errors import (
    DuplicateResourceError,
    ResourceNotFoundError,
)


class InventoryService:
    """Read-only access to laboratory materials."""

    def __init__(self, items: Iterable[InventoryItem]) -> None:
        self._items_by_id: dict[str, InventoryItem] = {}

        for item in items:
            if item.id in self._items_by_id:
                raise DuplicateResourceError(
                    resource_type="inventory item",
                    resource_id=item.id,
                )

            self._items_by_id[item.id] = item

    def list_all(self) -> list[InventoryItem]:
        """Return all inventory items."""

        return list(self._items_by_id.values())

    def get(self, item_id: str) -> InventoryItem:
        """Return an inventory item by identifier."""

        try:
            return self._items_by_id[item_id]
        except KeyError as exc:
            raise ResourceNotFoundError(
                resource_type="inventory item",
                resource_id=item_id,
            ) from exc
