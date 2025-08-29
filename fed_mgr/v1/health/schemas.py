"""Schemas for health status endpoints.

Defines models representing the health status of the application and its dependencies.
"""

from typing import Annotated

from pydantic import computed_field
from sqlmodel import Field, SQLModel


class Health(SQLModel):
    """Represents the health status of the application."""

    db_connection: Annotated[bool, Field(description="Status of DB connection")]
    opa_connection: Annotated[
        bool | None, Field(default=None, description="Status of OPA connection")
    ]
    kafka_connection: Annotated[
        bool | None, Field(default=None, description="Status of Kafka connection")
    ]

    @computed_field
    @property
    def status(self) -> str:
        """General application status."""
        if (
            self.db_connection
            and self.opa_connection is not False
            and self.kafka_connection is not False
        ):
            return "healthy"
        return "unhealthy"
