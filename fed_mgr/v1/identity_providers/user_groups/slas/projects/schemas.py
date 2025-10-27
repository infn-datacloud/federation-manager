"""SLAs schemas returned by the endpoints."""

import uuid
from typing import Annotated

from sqlmodel import Field, SQLModel

from fed_mgr.v1.schemas import PaginationQuery, SortQuery


class ProjSLAConnectionCreate(SQLModel):
    """Schema with the basic parameters of the SLA entity."""

    project_id: Annotated[
        uuid.UUID, Field(description="The ID of the projet to connect")
    ]


class ProjSLAQuery(PaginationQuery, SortQuery):
    """Schema used to define request's body parameters."""
