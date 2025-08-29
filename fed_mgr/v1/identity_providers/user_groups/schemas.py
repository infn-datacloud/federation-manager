"""User Groups schemas returned by the endpoints."""

import urllib.parse
from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl, computed_field
from sqlmodel import Field, SQLModel

from fed_mgr.v1 import SLAS_PREFIX
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


class UserGroupRead(ItemID, CreationRead, EditableRead, UserGroupBase):
    """Schema used to read an Identity Provider."""

    base_url: Annotated[
        AnyHttpUrl, Field(exclude=True, description="Base URL for the children URL")
    ]

    @computed_field
    @property
    def links(self) -> UserGroupLinks:
        """Build the slas endpoints in the UserGroupLinks object.

        Returns:
            UserGroupLinks: An object with the user_groups attribute.

        """
        link = urllib.parse.urljoin(str(self.base_url), f"{self.id}{SLAS_PREFIX}")
        return UserGroupLinks(slas=link)


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
