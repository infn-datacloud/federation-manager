"""SLAs schemas returned by the endpoints."""

import uuid
from typing import Annotated

from sqlmodel import Field, SQLModel


class ProjSLAConnectionCreate(SQLModel):
    """Schema with the basic parameters of the SLA entity."""

    project_id: Annotated[
        uuid.UUID, Field(description="The ID of the projet to connect")
    ]
