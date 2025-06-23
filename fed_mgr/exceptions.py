"""Custom common exceptions."""


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
