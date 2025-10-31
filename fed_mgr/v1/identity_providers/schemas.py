"""Identity Providers schemas returned by the endpoints.

This module defines the data models used to represent Identity Providers and their
related attributes. These schemas are used for validating and serializing data exchanged
between the application and clients through the Identity Providers endpoints.

Classes:
    - IdentityProviderBase: Defines the basic parameters of an Identity Provider.
    - IdentityProviderCreate: Schema for creating a new Identity Provider.
    - IdentityProviderLinks: Contains links related to an Identity Provider.
    - IdentityProviderRead: Schema for reading Identity Provider details.
    - IdentityProviderList: Schema for returning a paginated list of Identity Providers.
    - IdentityProviderQuery: Schema for defining query parameters for Identity
        Providers.
"""

import urllib.parse
from typing import Annotated

from pydantic import AnyHttpUrl, computed_field
from sqlmodel import Field, SQLModel

from fed_mgr.v1 import USER_GROUPS_PREFIX
from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    DescriptionQuery,
    EditableQuery,
    EditableRead,
    HttpUrlType,
    ItemDescription,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class IdentityProviderBase(ItemDescription):
    """Schema with the basic parameters of the Identity Provider entity.

    Attributes:
        endpoint (AnyHttpUrl): The endpoint of the Identity Provider.
        name (str): A friendly name for the Identity Provider, used during
            authentication.
        groups_claim (str): The claim name to retrieve user groups or roles.
        protocol (str | None): The protocol used for authentication.
        audience (str | None): The audience for authentication.

    """

    endpoint: Annotated[
        AnyHttpUrl,
        Field(
            sa_type=HttpUrlType,
            unique=True,
            description="Endpoint of the Identity Provider",
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Friendly name of the identity provider. It should be used by "
            "the resource provider to connect to it during authentication procedures"
        ),
    ]
    groups_claim: Annotated[
        str,
        Field(description="Name of the claim from which retrieve user groups or roles"),
    ]
    protocol: Annotated[
        str | None,
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


class IdentityProviderCreate(IdentityProviderBase):
    """Schema used to create an Identity Provider.

    Inherits:
        IdentityProviderBase: Includes all attributes from the base schema.

    Attributes:
        endpoint (AnyHttpUrl): The endpoint of the Identity Provider.
        name (str): A friendly name for the Identity Provider, used during
            authentication.
        groups_claim (str): The claim name to retrieve user groups or roles.
        protocol (str | None): The protocol used for authentication.
        audience (str | None): The audience for authentication.

    """


class IdentityProviderLinks(SQLModel):
    """Schema containing links related to the Identity Provider.

    Attributes:
        user_groups (AnyHttpUrl): Link to retrieve the list of user groups for this
            Identity Provider.

    """

    user_groups: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the list of user groups belonging to this "
            "identity provider."
        ),
    ]


class IdentityProviderRead(ItemID, CreationRead, EditableRead, IdentityProviderBase):
    """Schema used to read an Identity Provider.

    Inherits:
        IdentityProviderBase: Includes all attributes from the base schema.
        ItemID: Adds the unique identifier for the Identity Provider.
        CreationRead: Adds creation metadata.
        EditableRead: Adds editable metadata.

    Attributes:
        endpoint (AnyHttpUrl): The endpoint of the Identity Provider.
        name (str): A friendly name for the Identity Provider, used during
            authentication.
        groups_claim (str): The claim name to retrieve user groups or roles.
        protocol (str | None): The protocol used for authentication.
        audience (str | None): The audience for authentication.
        base_url (AnyHttpUrl): The base URL for constructing child URLs.
        links (IdentityProviderLinks): Links to related resources, such as user groups.

    """

    base_url: Annotated[
        AnyHttpUrl, Field(exclude=True, description="Base URL for the children URL")
    ]

    @computed_field
    @property
    def links(self) -> IdentityProviderLinks:
        """Build the user groups endpoints in the IdentityProviderLinks object.

        Returns:
            IdentityProviderLinks: An object with the user_groups attribute.

        """
        link = urllib.parse.urljoin(
            str(self.base_url), f"{self.id}{USER_GROUPS_PREFIX}"
        )
        return IdentityProviderLinks(user_groups=link)


class IdentityProviderList(PaginatedList):
    """Schema used to return paginated list of Identity Providers' data to clients.

    Inherits:
        PaginatedList: Includes pagination metadata.

    Attributes:
        total (int): The total number of items available.
        page (int): The current page number.
        size (int): The number of items per page.
        data (list[IdentityProviderRead]): A list of Identity Providers, including all
            attributes from IdentityProviderRead.

    """

    data: Annotated[
        list[IdentityProviderRead],
        Field(default_factory=list, description="List of identity providers"),
    ]


class IdentityProviderQuery(
    DescriptionQuery, CreationQuery, EditableQuery, PaginationQuery, SortQuery
):
    """Schema used to define request's body parameters.

    Inherits:
        DescriptionQuery: Includes description-based query parameters.
        CreationQuery: Includes creation-based query parameters.
        EditableQuery: Includes editable-based query parameters.
        PaginationQuery: Includes pagination-based query parameters.
        SortQuery: Includes sorting-based query parameters.

    Attributes:
        endpoint (str | None): Filter for Identity Providers whose endpoint contains
            this string.
        name (str | None): Filter for Identity Providers whose name contains this
            string.
        groups_claim (str | None): Filter for Identity Providers whose groups_claim
            contains this string.
        protocol (str | None): Filter for Identity Providers whose protocol contains
            this string.
        audience (str | None): Filter for Identity Providers whose audience contains
            this string.

    """

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
