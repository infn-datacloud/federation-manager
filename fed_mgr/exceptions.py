"""Custom common exceptions."""

import uuid


class ConflictError(Exception):
    """Exception raised when there is a CONFLICT during a DB insertion."""

    def __init__(self, message):
        """Initialize ConflictError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class NotNullError(Exception):
    """Exception raised when a None value is not acceptale during DB insertion."""

    def __init__(self, message):
        """Initialize NotNullError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class NoItemToUpdateError(Exception):
    """Exception raised when the item is not found during DB update."""

    def __init__(self, message):
        """Initialize NoItemToUpdateError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class ProviderStateChangeError(Exception):
    """Exception raised when the proposed state change fails."""

    def __init__(self, message):
        """Initialize ProviderStateChangeError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class ItemNotFoundError(Exception):
    """Exception raised when the target ID does not match a user in the DB."""

    def __init__(self, entity: str, id: uuid.UUID):
        """Initialize ItemNotFoundError with a specific error message."""
        self.message = f"{entity} with ID '{id!s}' does not exist"
        super().__init__(self.message)


class LocationNotFoundError(Exception):
    """Exception raised when the target ID does not match a location in the DB."""

    def __init__(self, message):
        """Initialize LocationNotFoundError with a specific error message."""
        self.message = message
        super().__init__(self.message)


class DeleteFailedError(Exception):
    """Exception raised when the delete operations has no effect."""

    def __init__(self, message):
        """Initialize DeleteFailedError with a specific error message."""
        self.message = message
        super().__init__(self.message)
