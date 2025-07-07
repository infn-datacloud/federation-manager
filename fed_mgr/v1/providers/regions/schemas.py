"""Regions schemas returned by the endpoints."""

import uuid
from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl
from sqlmodel import AutoString, Field, SQLModel

from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    DescriptionQuery,
    EditableQuery,
    EditableRead,
    ItemDescription,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class RegionBase(ItemDescription):
    """Schema with the basic parameters of the Region entity."""

    name: Annotated[
        str,
        Field(
            default="default",
            description="For resource providers supporting multiple regions this value "
            "must match the resource provider region. Otherwise it is a placeholder.",
        ),
    ]


class RegionCreate(RegionBase):
    """Schema used to create a Region."""

    location_id: Annotated[
        uuid.UUID,
        Field(description="ID of the physical site hosting the region's resources."),
    ]


class RegionLinks(SQLModel):
    """Schema containing links related to the Region."""

    location: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the location hosting the region's resources."
        ),
    ]


class RegionRead(ItemID, CreationRead, EditableRead, RegionBase):
    """Schema used to read an Region."""

    links: Annotated[
        RegionLinks,
        Field(
            sa_type=AutoString,
            description="Dict with the links of the resource project related entities",
        ),
    ]


class RegionList(PaginatedList):
    """Schema used to return paginated list of Regions' data to clients."""

    data: Annotated[
        list[RegionRead],
        Field(default_factory=list, description="List of resource projects"),
    ]


class RegionQuery(
    DescriptionQuery, CreationQuery, EditableQuery, PaginationQuery, SortQuery
):
    """Schema used to define request's body parameters."""

    name: Annotated[
        str | None,
        Field(default=None, description="Region name must contain this string"),
    ]


RegionQueryDep = Annotated[RegionQuery, Query()]
