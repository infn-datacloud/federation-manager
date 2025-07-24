"""Providers schemas returned by the endpoints."""

import uuid
from enum import Enum
from typing import Annotated

from fastapi import Query
from pydantic import AfterValidator, AnyHttpUrl, EmailStr, computed_field
from sqlmodel import JSON, AutoString, Column, Field, SQLModel

from fed_mgr.utils import HttpUrlType, check_list_not_empty
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


class ProviderType(str, Enum):
    """Enumeration of supported resource provider types."""

    openstack = "openstack"
    kubernetes = "kubernetes"


class ProviderStatus(int, Enum):
    """Enumeration of possible resource provider statuses."""

    draft = 0
    submitted = 1
    ready = 2
    evaluation = 3
    pre_production = 4
    active = 5
    deprecated = 6
    removed = 7
    degraded = 8
    maintenance = 9
    re_evaluation = 10


class ProviderBase(ItemDescription):
    """Schema with the basic parameters of the Provider entity."""

    name: Annotated[
        str, Field(unique=True, description="Friendly name of the resource provider")
    ]
    type: Annotated[
        ProviderType,
        Field(
            description="Resource provider type. Allowed values: openstack, kubernetes"
        ),
    ]
    auth_endpoint: Annotated[
        AnyHttpUrl,
        Field(
            sa_type=HttpUrlType,
            unique=True,
            description="Authentication URL of the resource provider",
        ),
    ]
    is_public: Annotated[
        bool,
        Field(default=False, description="Define if the provider is public or not"),
    ]
    support_emails: Annotated[
        list[EmailStr],
        Field(
            sa_column=Column(JSON),
            description="Non-empty list of Provider's admins/support email addresses",
        ),
        AfterValidator(check_list_not_empty),
    ]
    image_tags: Annotated[
        list[str],
        Field(
            default_factory=list,
            sa_column=Column(JSON),
            description="List of tags used to filter provider images (used only with "
            "'openstack' provider types)",
        ),
    ]
    network_tags: Annotated[
        list[str],
        Field(
            default_factory=list,
            sa_column=Column(JSON),
            description="List of tags used to filter provider networks (used only with "
            "'openstack' provider types)",
        ),
    ]


class ProviderInternal(SQLModel):
    """Schema with the attributes which can't be used when creating an instnce."""

    status: Annotated[
        ProviderStatus,
        Field(default=ProviderStatus.draft, description="Resource provider status"),
    ]


class ProviderCreate(ProviderBase):
    """Schema used to create a Provider."""

    site_admins: Annotated[
        list[uuid.UUID],
        Field(
            sa_type=AutoString,
            description="List of the provider/site administrator IDs",
        ),
        AfterValidator(check_list_not_empty),
    ]


class ProviderUpdate(SQLModel):
    """Schema used to update singe fields of a Provider.

    It is not possible to update the provider's type or the status.
    To udpate the status field a dedicated endpoint exists.
    """

    description: Annotated[
        str | None, Field(default=None, description="Item decription")
    ]
    name: Annotated[
        str | None,
        Field(
            default=None,
            unique=True,
            description="Friendly name of the resource provider",
        ),
    ]
    auth_endpoint: Annotated[
        AnyHttpUrl | None,
        Field(
            default=None,
            sa_type=HttpUrlType,
            unique=True,
            description="Authentication URL of the resource provider",
        ),
    ]
    is_public: Annotated[
        bool | None,
        Field(default=None, description="Define if the provider is public or not"),
    ]
    support_emails: Annotated[
        list[EmailStr] | None,
        Field(
            default=None,
            sa_type=AutoString,
            description="Non-empty list of Provider's admins/support email addresses",
        ),
        AfterValidator(check_list_not_empty),
    ]
    image_tags: Annotated[
        list[str] | None,
        Field(
            default=None,
            sa_type=AutoString,
            description="List of tags used to filter provider images (used only with "
            "'openstack' provider types)",
        ),
    ]
    network_tags: Annotated[
        list[str] | None,
        Field(
            default=None,
            sa_type=AutoString,
            description="List of tags used to filter provider networks (used only with "
            "'openstack' provider types)",
        ),
    ]
    site_admins: Annotated[
        list[uuid.UUID] | None,
        Field(
            default=None,
            sa_type=AutoString,
            description="List of the provider/site administrator IDs",
        ),
        AfterValidator(check_list_not_empty),
    ]
    site_testers: Annotated[
        list[uuid.UUID] | None,
        Field(
            default=None,
            sa_type=AutoString,
            description="List of the provider/site testers IDs",
        ),
    ]


class ProviderLinks(SQLModel):
    """Schema containing links related to the Provider."""

    idps: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the list of resource providers trusted by "
            "the resource provider."
        ),
    ]
    projects: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the list of projects belonging to the "
            "resource provider."
        ),
    ]
    regions: Annotated[
        AnyHttpUrl,
        Field(
            description="Link to retrieve the list of regions composing by the "
            "resource provider."
        ),
    ]


class ProviderRead(ItemID, CreationRead, EditableRead, ProviderBase, ProviderInternal):
    """Schema used to read an Provider."""

    site_admins: Annotated[
        list[uuid.UUID],
        Field(
            sa_type=AutoString,
            description="List of the provider/site administrator IDs",
        ),
    ]
    site_testers: Annotated[
        list[uuid.UUID] | None,
        Field(
            default=None,
            sa_type=AutoString,
            description="List of the provider/site testers IDs",
        ),
    ]
    links: Annotated[
        ProviderLinks,
        Field(
            sa_type=AutoString,
            description="Dict with the links of the resource provider related entities",
        ),
    ]

    @computed_field
    @property
    def status_name(self) -> str:
        """Status name for human readability."""
        return self.status.name


class ProviderList(PaginatedList):
    """Schema used to return paginated list of Providers' data to clients."""

    data: Annotated[
        list[ProviderRead],
        Field(default_factory=list, description="List of resource providers"),
    ]


class ProviderQuery(
    DescriptionQuery, CreationQuery, EditableQuery, PaginationQuery, SortQuery
):
    """Schema used to define request's body parameters."""

    name: Annotated[
        str | None,
        Field(
            default=None, description="Resource provider name must contain this string"
        ),
    ]
    type: Annotated[
        str | None,
        Field(
            default=None, description="Resource provider type must contain this string"
        ),
    ]
    auth_endpoint: Annotated[
        str | None,
        Field(
            default=None,
            description="Resource provider authentication URL must contain this string",
        ),
    ]
    is_public: Annotated[
        bool | None,
        Field(default=None, description="Resource provider must be public or not"),
    ]
    support_emails: Annotated[
        str | None,
        Field(
            default=None,
            description="Any of the resource provider support emails must contain this "
            "string",
        ),
    ]
    image_tags: Annotated[
        str | None,
        Field(
            default=None,
            description="Any of the resource provider image tagss must contain this "
            "string",
        ),
    ]
    network_tags: Annotated[
        str | None,
        Field(
            default=None,
            description="Any of the resource provider network tagss must contain this "
            "string",
        ),
    ]
    status: Annotated[
        str | None, Field(default=None, description="Resource provider status")
    ]
    site_admins: Annotated[
        str | None,
        Field(
            default=None,
            description="Any of the provider/site administrators IDs must contain this "
            "string",
        ),
    ]
    site_testers: Annotated[
        str | None,
        Field(
            default=None,
            description="Any of the provider/site testers IDs must contain this string",
        ),
    ]


ProviderQueryDep = Annotated[ProviderQuery, Query()]
