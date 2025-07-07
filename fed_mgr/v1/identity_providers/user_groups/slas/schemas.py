"""SLAs schemas returned by the endpoints."""

from datetime import date, datetime
from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl
from sqlmodel import TIMESTAMP, AutoString, Field, SQLModel

from fed_mgr.utils import HttpUrlType
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


class SLABase(ItemDescription):
    """Schema with the basic parameters of the SLA entity."""

    name: Annotated[str, Field(description="Name of the user group in the user group")]
    url: Annotated[
        AnyHttpUrl,
        Field(
            sa_type=HttpUrlType,
            unique=True,
            description="Link where the physical SLA is stored",
        ),
    ]
    start_date: Annotated[
        date,
        Field(
            sa_type=TIMESTAMP(timezone=True),
            description="The SLA is valid starting from this date",
        ),
    ]
    end_date: Annotated[
        date,
        Field(
            sa_type=TIMESTAMP(timezone=True),
            description="The SLA is valid before this date",
        ),
    ]


class SLACreate(SLABase):
    """Schema used to create an SLA."""


class SLALinks(SQLModel):
    """Schema containing links related to the Identity Provider."""

    projects: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the list of Projects pointed by to this SLA"
        ),
    ]


class SLARead(ItemID, CreationRead, EditableRead, SLABase):
    """Schema used to read an Identity Provider."""

    links: Annotated[
        SLALinks,
        Field(
            sa_type=AutoString,
            description="Dict with the links of the user groups related entities",
        ),
    ]


class SLAList(PaginatedList):
    """Schema used to return paginated list of SLAs' data to clients."""

    data: Annotated[
        list[SLARead], Field(default_factory=list, description="List of slas")
    ]


class SLAQuery(
    DescriptionQuery, CreationQuery, EditableQuery, PaginationQuery, SortQuery
):
    """Schema used to define request's body parameters."""

    name: Annotated[
        str | None,
        Field(default=None, description="SLA name must contain this string"),
    ]
    url: Annotated[
        str | None, Field(default=None, description="SLA url must contain this string")
    ]
    start_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's start date must be lower than or equal to this value",
        ),
    ]
    start_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's start date must be greater than or equal to this value",
        ),
    ]
    end_before: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's end date must be lower than or equal to this value",
        ),
    ]
    end_after: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Item's end date must be greater than or equal to this value",
        ),
    ]


SLAQueryDep = Annotated[SLAQuery, Query()]
