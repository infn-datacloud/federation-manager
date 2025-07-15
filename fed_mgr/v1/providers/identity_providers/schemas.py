"""Identity Providers schemas returned by the endpoints."""

import uuid
from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl
from sqlmodel import AutoString, Field, SQLModel

from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    EditableQuery,
    EditableRead,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class ProviderIdPConnectionBase(SQLModel):
    """Schema with the parameters to overwrite when connecting Providers with IdPs."""

    groups_claim: Annotated[
        str | None,
        Field(
            default=None,
            description="Name of the claim from which retrieve user groups or roles. "
            "Override the IdP default one.",
        ),
    ]
    name: Annotated[
        str | None,
        Field(
            default=None,
            description="Name used by the resource provider to connect to this IdP "
            "during it during authentication procedures. Override the IdP default one.",
        ),
    ]
    protocol: Annotated[
        str | None,
        Field(
            default=None,
            description="Name of the protocol used by the resource provider to connect "
            "to this identity provider during authentication procedures. Override the "
            "IdP default one.",
        ),
    ]
    audience: Annotated[
        str | None,
        Field(
            default=None,
            description="Name of the audience the resource provider can use to connect "
            "to this identity provider during authentication procedures. Override the "
            "IdP default one.",
        ),
    ]


class ProviderIdPConnectionCreate(ProviderIdPConnectionBase):
    """Schema used to connect a Provider to an Identity Provider."""


class ProviderIdPConnectionLinks(SQLModel):
    """Schema containing links related to the Provider."""

    idp: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the Identity Provider default configuration."
        ),
    ]


class ProviderIdPConnectionRead(CreationRead, EditableRead, ProviderIdPConnectionBase):
    """Schema used to read an Identity Provider."""

    provider_id: Annotated[uuid.UUID, Field(description="Resource provider ID")]
    idp_id: Annotated[uuid.UUID, Field(description="Identity Provider ID")]
    links: Annotated[
        ProviderIdPConnectionLinks,
        Field(
            sa_type=AutoString,
            description="Dict with the links of the relationship related entities",
        ),
    ]


class ProviderIdPConnectionList(PaginatedList):
    """Schema used to return paginated list of Identity Providers' data to clients."""

    data: Annotated[
        list[ProviderIdPConnectionRead],
        Field(
            default_factory=list,
            description="List of provider - identity provider connections",
        ),
    ]


class ProviderIdPConnectionQuery(
    CreationQuery, EditableQuery, PaginationQuery, SortQuery
):
    """Schema used to define request's body parameters."""

    idp_id: Annotated[
        str | None,
        Field(
            default=None,
            description="Identity Provider ID must contain this string",
        ),
    ]
    name: Annotated[
        str | None,
        Field(
            default=None,
            description="Identity Provider overridden name must contain this string",
        ),
    ]
    groups_claim: Annotated[
        str | None,
        Field(
            default=None,
            description="Identity Provider overridden groups_claim must contain this "
            "string",
        ),
    ]
    protocol: Annotated[
        str | None,
        Field(
            default=None,
            description="Identity Provider overridden protocol must contain this "
            "string",
        ),
    ]
    audience: Annotated[
        str | None,
        Field(
            default=None,
            description="Identity Provider overridden audience must contain this "
            "string",
        ),
    ]


ProviderIdPConnectionQueryDep = Annotated[ProviderIdPConnectionQuery, Query()]
