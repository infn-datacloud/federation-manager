"""SLAs schemas returned by the endpoints."""

import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl
from sqlmodel import TIMESTAMP, AutoString, Field, SQLModel

from fed_mgr.utils import HttpUrlType
from fed_mgr.v1.schemas import (
    Creation,
    CreationQuery,
    Editable,
    EditableQuery,
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
            description="Link where the physical SLA is stored",
            sa_type=HttpUrlType,
            unique=True,
        ),
    ]
    start_date: Annotated[
        date,
        Field(
            description="The SLA is valid starting from this date",
            sa_type=TIMESTAMP(timezone=True),
        ),
    ]
    end_date: Annotated[
        date,
        Field(
            description="The SLA is valid before this date",
            sa_type=TIMESTAMP(timezone=True),
        ),
    ]


class SLA(ItemID, Creation, Editable, SLABase, table=True):
    """Schema used to return SLA's data to clients."""

    user_group: Annotated[
        uuid.UUID,
        Field(description="Parent user group", foreign_key="usergroup.id"),
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


class SLARead(ItemID, Creation, Editable, SLABase):
    """Schema used to read an Identity Provider."""

    links: Annotated[
        SLALinks,
        Field(
            description="Dict with the links of the user groups related entities",
            sa_type=AutoString,
        ),
    ]


class SLAList(PaginatedList):
    """Schema used to return paginated list of SLAs' data to clients."""

    data: Annotated[
        list[SLARead], Field(default_factory=list, description="List of slas")
    ]


class SLAQuery(CreationQuery, EditableQuery, PaginationQuery, SortQuery):
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
