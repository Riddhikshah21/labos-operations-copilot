"""Errors raised by the LabOS SDK."""


class LabOSError(Exception):
    """Base exception for LabOS client errors."""


class ResourceNotFoundError(LabOSError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id

        super().__init__(
            f"{resource_type} resource not found: {resource_id}",
        )


class DuplicateResourceError(LabOSError):
    """Raised when fixture data contains duplicate identifiers."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id

        super().__init__(
            f"Duplicate {resource_type} resource: {resource_id}",
        )
