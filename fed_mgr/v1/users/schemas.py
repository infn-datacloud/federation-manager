"""Users schemas returned by the endpoints."""

from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl, EmailStr
from sqlmodel import AutoString, Field, SQLModel

from fed_mgr.utils import HttpUrlType
from fed_mgr.v1.schemas import (
    CreationTimeQuery,
    CreationTimeRead,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class UserBase(SQLModel):
    """Schema with the basic parameters of the User entity."""

    sub: Annotated[str, Field(description="Issuer's subject associated with this user")]
    name: Annotated[str, Field(description="User name and surname")]
    email: Annotated[
        EmailStr, Field(sa_type=AutoString, description="User email address")
    ]
    issuer: Annotated[AnyHttpUrl, Field(sa_type=HttpUrlType, description="Issuer URL")]


class UserCreate(UserBase):
    """Schema used to define request's body parameters of a POST on 'users' endpoint."""


class UserRead(ItemID, CreationTimeRead, UserBase):
    """Schema used to return User's data to clients."""


class UserList(PaginatedList):
    """Schema used to return paginated list of Users' data to clients."""

    data: Annotated[
        list[UserRead], Field(default_factory=list, description="List of users")
    ]


class UserQuery(CreationTimeQuery, PaginationQuery, SortQuery):
    """Schema used to define request's body parameters."""

    sub: Annotated[
        str | None,
        Field(default=None, description="User's subject must contain this string"),
    ]
    name: Annotated[
        str | None,
        Field(default=None, description="User's name must contains this string"),
    ]
    email: Annotated[
        str | None,
        Field(
            default=None, description="User's email address must contain this string"
        ),
    ]
    issuer: Annotated[
        str | None,
        Field(default=None, description="User's issuer URL must contain this string"),
    ]


UserQueryDep = Annotated[UserQuery, Query()]
