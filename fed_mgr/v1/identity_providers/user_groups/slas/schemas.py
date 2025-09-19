"""SLAs schemas returned by the endpoints."""

import urllib.parse
from datetime import date
from typing import Annotated

from pydantic import AnyHttpUrl, computed_field
from sqlmodel import TIMESTAMP, Field, SQLModel

from fed_mgr.utils import HttpUrlType
from fed_mgr.v1 import PROJECTS_PREFIX
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

    base_url: Annotated[
        AnyHttpUrl, Field(exclude=True, description="Base URL for the children URL")
    ]

    @computed_field
    @property
    def links(self) -> SLALinks:
        """Build the slas endpoints in the SLALinks object.

        Returns:
            SLALinks: An object with the user_groups attribute.

        """
        link = urllib.parse.urljoin(str(self.base_url), f"{self.id}{PROJECTS_PREFIX}")
        return SLALinks(projects=link)


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
        date | None,
        Field(
            default=None,
            description="Item's start date must be lower than or equal to this value",
        ),
    ]
    start_after: Annotated[
        date | None,
        Field(
            default=None,
            description="Item's start date must be greater than or equal to this value",
        ),
    ]
    end_before: Annotated[
        date | None,
        Field(
            default=None,
            description="Item's end date must be lower than or equal to this value",
        ),
    ]
    end_after: Annotated[
        date | None,
        Field(
            default=None,
            description="Item's end date must be greater than or equal to this value",
        ),
    ]
