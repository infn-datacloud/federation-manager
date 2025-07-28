"""Identity Providers schemas returned by the endpoints."""

import uuid
from typing import Annotated

from fastapi import Query
from pydantic import AnyHttpUrl, computed_field
from sqlmodel import Field, SQLModel

from fed_mgr.v1 import IDPS_PREFIX, PROVIDERS_PREFIX
from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    EditableQuery,
    EditableRead,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class IdpOverridesBase(SQLModel):
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


class ProviderIdPConnectionCreate(SQLModel):
    """Schema used to connect a Provider to an Identity Provider."""

    idp_id: Annotated[uuid.UUID, Field(description="Identity Provider ID")]
    overrides: Annotated[
        IdpOverridesBase,
        Field(description="Parameters to override for the target identity provider"),
    ]


class ProviderIdPConnectionLinks(SQLModel):
    """Schema containing links related to the Provider."""

    idps: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the Identity Provider default configuration."
        ),
    ]


class ProviderIdPConnectionRead(CreationRead, EditableRead):
    """Schema used to read an Identity Provider."""

    idp_id: Annotated[uuid.UUID, Field(description="Identity Provider ID")]
    overrides: Annotated[
        IdpOverridesBase,
        Field(description="Parameters to override for the target identity provider"),
    ]
    base_url: Annotated[
        AnyHttpUrl, Field(exclude=True, description="Base URL for the children URL")
    ]

    @computed_field
    @property
    def links(self) -> ProviderIdPConnectionLinks:
        """Build the slas endpoints in the ProviderIdPConnectionLinks object.

        Returns:
            ProviderIdPConnectionLinks: An object with the user_groups attribute.

        """
        link = str(self.base_url)
        link = link[: link.index(PROVIDERS_PREFIX)] + IDPS_PREFIX
        return ProviderIdPConnectionLinks(idps=link)


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
