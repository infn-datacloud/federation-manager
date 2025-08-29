"""Locations schemas returned by the endpoints."""

from typing import Annotated

from fastapi import Query
from sqlmodel import Field

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


class LocationBase(ItemDescription):
    """Schema with the basic parameters of the Location entity."""

    name: Annotated[
        str, Field(unique=True, description="Friendly name of the location.")
    ]
    country: Annotated[
        str,
        Field(description="Country code of the site (ISO 3166-1 alpha-2 country code)"),
    ]
    lat: Annotated[
        float | None,
        Field(default=None, ge=-90, le=90, description="Latitude"),
    ]
    lon: Annotated[
        float | None,
        Field(default=None, ge=-180, le=180, description="Longitude"),
    ]


class LocationCreate(LocationBase):
    """Schema used to create an Location."""


class LocationRead(ItemID, CreationRead, EditableRead, LocationBase):
    """Schema used to read an Location."""


class LocationList(PaginatedList):
    """Schema used to return paginated list of Locations' data to clients."""

    data: Annotated[
        list[LocationRead],
        Field(default_factory=list, description="List of locations"),
    ]


class LocationQuery(
    DescriptionQuery, CreationQuery, EditableQuery, PaginationQuery, SortQuery
):
    """Schema used to define request's body parameters."""

    name: Annotated[
        str | None,
        Field(default=None, description="Location name must contain this string."),
    ]
    country: Annotated[
        str | None,
        Field(
            default=None,
            description="Location's country code must contain this string.",
        ),
    ]
    lat_gte: Annotated[
        float | None,
        Field(
            default=None,
            description="Location's latitude must be greater than or equal.",
        ),
    ]
    lat_lte: Annotated[
        float | None,
        Field(
            default=None,
            description="Location's latitude must be lower than or equal.",
        ),
    ]
    lon_gte: Annotated[
        float | None,
        Field(
            default=None,
            description="Location's longitude must be greater than or equal.",
        ),
    ]
    lon_lte: Annotated[
        float | None,
        Field(
            default=None,
            description="Location's longitude must be lower than or equal.",
        ),
    ]


LocationQueryDep = Annotated[LocationQuery, Query()]
