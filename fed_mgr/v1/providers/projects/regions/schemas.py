"""ProjRegConnections's configurations schemas returned by the endpoints."""

import urllib.parse
import uuid
from typing import Annotated

from pydantic import AnyHttpUrl, computed_field
from sqlmodel import Field, SQLModel

from fed_mgr.v1 import REGIONS_PREFIX
from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    EditableQuery,
    EditableRead,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class RegionOverridesBase(SQLModel):
    """Schema with the basic parameters of the ProjRegConnection entity."""

    default_public_net: Annotated[
        str | None, Field(default=None, description="The default public net to use")
    ]
    default_private_net: Annotated[
        str | None, Field(default=None, description="The default private net to use")
    ]
    private_net_proxy_host: Annotated[
        str | None,
        Field(
            default=None,
            description="The proxy VM hostname (and port) to use to reach via SSH the "
            "private net",
        ),
    ]
    private_net_proxy_user: Annotated[
        str | None,
        Field(
            default=None,
            description="The proxy VM username to use to reach via SSH the private net",
        ),
    ]


class ProjRegConnectionCreate(SQLModel):
    """Schema used to create a ProjRegConnection."""

    region_id: Annotated[uuid.UUID, Field(description="Region ID")]
    overrides: Annotated[
        RegionOverridesBase,
        Field(description="The project overrides for the target region"),
    ]


class ProjRegConnectionLinks(SQLModel):
    """Schema containing links related to the ProjRegConnection."""

    regions: Annotated[
        AnyHttpUrl, Field(description="Link to retrieve the target region.")
    ]


class ProjRegConnectionRead(CreationRead, EditableRead):
    """Schema used to read an ProjRegConnection."""

    region_id: Annotated[uuid.UUID, Field(description="Region ID")]
    overrides: Annotated[
        RegionOverridesBase,
        Field(description="The project overrides for the target region"),
    ]
    base_url: Annotated[
        AnyHttpUrl, Field(exclude=True, description="Base URL for the children URL")
    ]

    @computed_field
    @property
    def links(self) -> ProjRegConnectionLinks:
        """Build the slas endpoints in the ProjRegConnectionLinks object.

        Returns:
            ProjRegConnectionLinks: An object with the user_groups attribute.

        """
        link = urllib.parse.urljoin(str(self.base_url), f"{REGIONS_PREFIX}")
        return ProjRegConnectionLinks(regions=link)


class ProjRegConnectionList(PaginatedList):
    """Schema used to return paginated list of ProjRegConnections' data to clients."""

    data: Annotated[
        list[ProjRegConnectionRead],
        Field(default_factory=list, description="List of projects configurations"),
    ]


class ProjRegConnectionQuery(CreationQuery, EditableQuery, PaginationQuery, SortQuery):
    """Schema used to define request's body parameters."""

    region_id: Annotated[
        str | None,
        Field(
            default=None, description="The linked region ID must contain this string."
        ),
    ]
    default_public_net: Annotated[
        str | None, Field(default=None, description="The default public net to use")
    ]
    default_private_net: Annotated[
        str | None, Field(default=None, description="The default private net to use")
    ]
    private_net_proxy_host: Annotated[
        str | None,
        Field(
            default=None,
            description="The proxy VM hostname (and port) to use to reach via SSH the "
            "private net",
        ),
    ]
    private_net_proxy_user: Annotated[
        str | None,
        Field(
            default=None,
            description="The proxy VM username to use to reach via SSH the private net",
        ),
    ]
