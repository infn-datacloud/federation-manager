"""Custom common exceptions."""

import uuid
from typing import Any

from fed_mgr.v1.providers.schemas import ProviderStatus


class ConflictError(Exception):
    """Exception raised when there is a CONFLICT during a DB insertion."""

    def __init__(self, entity: str, attr: str, value: Any):
        """Initialize ConflictError with a specific error message."""
        self.entity = entity
        self.attr = attr
        self.value = value
        if self.value is None:
            self.message = f"{self.entity} with {self.attr} already exists"
        else:
            self.message = f"{self.entity} with {self.attr}={self.value!s} already "
            self.message += "exists"
        super().__init__(self.message)


class NotNullError(Exception):
    """Exception raised when a None value is not acceptale during DB insertion."""

    def __init__(self, entity: str, attr: str):
        """Initialize NotNullError with a specific error message."""
        self.entity = entity
        self.attr = attr
        self.message = f"Attribute '{attr}' of {entity} can't be NULL"
        super().__init__(self.message)


class ProviderStateChangeError(Exception):
    """Exception raised when the proposed state change fails."""

    def __init__(self, start_state: ProviderStatus, end_state: ProviderStatus):
        """Initialize ProviderStateChangeError with a specific error message."""
        self.message = f"Transition from state '{start_state.name}' to state "
        self.message += f"'{end_state.name}' is forbidden"
        super().__init__(self.message)


class ItemNotFoundError(Exception):
    """Exception raised when the target ID does not match a user in the DB."""

    def __init__(
        self,
        entity: str,
        *,
        id: uuid.UUID | None = None,
        params: dict[str, Any] | None = None,
    ):
        """Initialize ItemNotFoundError with a specific error message."""
        self.entity = entity
        self.entity_id = id
        self.entity_params = params
        if id is not None:
            self.message = f"{self.entity} with ID '{self.entity_id!s}' does not exist"
        else:
            self.message = f"{self.entity} with given key-value pairs does not exist: "
            self.message += f"{self.entity_params!s}"
        super().__init__(self.message)


class DeleteFailedError(Exception):
    """Exception raised when the delete operations has no effect."""

    def __init__(
        self,
        entity: str,
        *,
        id: uuid.UUID | None = None,
        params: dict[str, Any] | None = None,
    ):
        """Initialize DeleteFailedError with a specific error message."""
        self.entity = entity
        self.entity_id = id
        self.entity_params = params
        if id is not None:
            self.message = f"{self.entity} with ID '{self.entity_id}' can't be deleted."
        else:
            self.message = f"{self.entity} with given key-value pairs does not exist: "
            self.message += f"{self.entity_params!s}."
        self.message += f" Check target {self.entity} has no children entities."
        super().__init__(self.message)


class KafkaError(Exception):
    """Exception raised when communicating with kafka."""

    def __init__(self):
        """Initialize KafkaError with a specific error message."""
        self.message = "Communication with kafka failed."
        super().__init__(self.message)


class DatabaseOperationError(Exception):
    """Generic Database erorr raised by an invalid operation."""

    def __init__(self, message: str):
        """Initialize KafkaError with a specific error message."""
        self.message = message
        super().__init__(self.message)
