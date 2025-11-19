"""Schemas for health status endpoints.

This module defines the data models used to represent the health status of the
application and its dependencies. These schemas are used for validating and serializing
the health status data returned by the health check endpoints.

Classes:
    - Health: Represents the health status of the application, including the status of
      the database, OPA, and Kafka connections.
"""

from typing import Annotated

from pydantic import computed_field
from sqlmodel import Field, SQLModel


class Health(SQLModel):
    """Represents the health status of the application.

    Attributes:
        db_connection (bool): Indicates whether the database connection is active.
        opa_connection (bool | None): Indicates whether the OPA connection is active.
        kafka_connection (bool | None): Indicates whether the Kafka connection is
            active.

    Properties:
        status (str): Returns the overall health status of the application as "healthy"
            or "unhealthy" based on the status of its dependencies.

    """

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
