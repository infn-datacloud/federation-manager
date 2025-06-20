"""Users schemas returned by the endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl, EmailStr
from sqlmodel import AutoString, Field, SQLModel, UniqueConstraint, func

from fed_mgr.utils import HttpUrlType
from fed_mgr.v1.schemas import (
    CreationQuery,
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
        EmailStr, Field(description="User email address", sa_type=AutoString)
    ]
    issuer: Annotated[AnyHttpUrl, Field(description="Issuer URL", sa_type=HttpUrlType)]


class User(ItemID, UserBase, table=True):
    """Schema used to return User's data to clients."""

    created_at: Annotated[
        datetime,
        Field(
            description="Date time of when the entity has been created",
            default=func.now(),
        ),
    ]

    __table_args__ = (
        UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
    )


class UserCreate(UserBase):
    """Schema used to define request's body parameters of a POST on 'users' endpoint."""


class UserQuery(CreationQuery, PaginationQuery, SortQuery):
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


class UserList(PaginatedList):
    """Schema used to return paginated list of Users' data to clients."""

    data: Annotated[
        list[User], Field(default_factory=list, description="List of users")
    ]


UserQueryDep = Annotated[UserQuery, Query()]
