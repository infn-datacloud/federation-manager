"""User Groups schemas returned by the endpoints."""

from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl
from sqlmodel import AutoString, Field, SQLModel

from fed_mgr.v1.schemas import (
    Creation,
    CreationQuery,
    DescriptionQuery,
    Editable,
    EditableQuery,
    ItemDescription,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class UserGroupBase(ItemDescription):
    """Schema with the basic parameters of the User Group entity."""

    name: Annotated[str, Field(description="Name of the user group in the user group")]


class UserGroupCreate(UserGroupBase):
    """Schema used to create an User Group."""


class UserGroupLinks(SQLModel):
    """Schema containing links related to the Identity Provider."""

    slas: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the list of SLAs signed by to this user group"
        ),
    ]


class UserGroupRead(ItemID, Creation, Editable, UserGroupBase):
    """Schema used to read an Identity Provider."""

    links: Annotated[
        UserGroupLinks,
        Field(
            sa_type=AutoString,
            description="Dict with the links of the user groups related entities",
        ),
    ]


class UserGroupList(PaginatedList):
    """Schema used to return paginated list of User Groups' data to clients."""

    data: Annotated[
        list[UserGroupRead], Field(default_factory=list, description="List of users")
    ]


class UserGroupQuery(
    DescriptionQuery, CreationQuery, EditableQuery, PaginationQuery, SortQuery
):
    """Schema used to define request's body parameters."""

    name: Annotated[
        str | None,
        Field(default=None, description="User Group name must contain this string"),
    ]


UserGroupQueryDep = Annotated[UserGroupQuery, Query()]
