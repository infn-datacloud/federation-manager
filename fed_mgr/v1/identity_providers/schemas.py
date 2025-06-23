"""Identity Providers schemas returned by the endpoints."""

from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl
from sqlmodel import Field

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


class IdentityProviderBase(ItemDescription):
    """Schema with the basic parameters of the Identity Provider entity."""

    endpoint: Annotated[
        AnyHttpUrl,
        Field(
            description="Endpoint of the Identity Provider",
            sa_type=HttpUrlType,
            unique=True,
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Freindly name of the identity provider. It should be used by "
            "the resource provider to connect to it during authentication procedures"
        ),
    ]
    groups_claim: Annotated[
        str,
        Field(description="Name of the claim from which retrieve user groups or roles"),
    ]
    protocol: Annotated[
        str,
        Field(
            default=None,
            description="Name of the protocol used by the resource provider to connect "
            "to this identity provider during authentication procedures",
        ),
    ]
    audience: Annotated[
        str | None,
        Field(
            default=None,
            description="Name of the audience the resource provider can use to connect "
            "to this identity provider during authentication procedures",
        ),
    ]


class IdentityProvider(ItemID, Creation, Editable, IdentityProviderBase, table=True):
    """Schema used to return Identity Provider's data to clients."""


class IdentityProviderList(PaginatedList):
    """Schema used to return paginated list of Identity Providers' data to clients."""

    data: Annotated[
        list[IdentityProvider], Field(default_factory=list, description="List of users")
    ]


class IdentityProviderCreate(IdentityProviderBase):
    """Schema used to create an Identity Provider."""


class IdentityProviderQuery(CreationQuery, EditableQuery, PaginationQuery, SortQuery):
    """Schema used to define request's body parameters."""

    endpoint: Annotated[
        str | None,
        Field(
            default=None,
            description="Identity Provider endpoint must contain this string",
        ),
    ]
    name: Annotated[
        str | None,
        Field(
            default=None, description="Identity Provider name must contain this string"
        ),
    ]
    groups_claim: Annotated[
        str | None,
        Field(
            default=None,
            description="Identity Provider groups_claim must contain this string",
        ),
    ]
    protocol: Annotated[
        str | None,
        Field(
            default=None,
            description="Identity Provider protocol must contain this string",
        ),
    ]
    audience: Annotated[
        str | None,
        Field(
            default=None,
            description="Identity Provider audience must contain this string",
        ),
    ]


IdentityProviderQueryDep = Annotated[IdentityProviderQuery, Query()]
