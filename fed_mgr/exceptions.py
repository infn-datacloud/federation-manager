"""Custom common exceptions."""


class ConflictError(Exception):
    """Exception raised when there is a CONFLICT during a DB insertion."""

    def __init__(self, message):
        """Initialize ConflictError with a specific error message."""
        self.message = message
        super().__init__(self.message)
