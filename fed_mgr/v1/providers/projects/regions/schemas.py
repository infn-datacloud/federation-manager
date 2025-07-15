"""ProjRegConfigs's configurations schemas returned by the endpoints."""

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
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


class ProjRegConfigBase(SQLModel):
    """Schema with the basic parameters of the ProjRegConfig entity."""

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


class ProjRegConfigCreate(ProjRegConfigBase):
    """Schema used to create a ProjRegConfig."""


class ProjRegConfigLinks(SQLModel):
    """Schema containing links related to the ProjRegConfig."""

    region: Annotated[
        AnyHttpUrl, Field(description="Link to retrieve the target region.")
    ]


class ProjRegConfigRead(ItemID, CreationRead, EditableRead, ProjRegConfigBase):
    """Schema used to read an ProjRegConfig."""

    project_id: Annotated[uuid.UUID, Field(description="Project ID")]
    region_id: Annotated[uuid.UUID, Field(description="Region ID")]
    links: Annotated[
        ProjRegConfigLinks,
        Field(
            sa_type=AutoString,
            description="Dict with the links of the related entities",
        ),
    ]


class ProjRegConfigList(PaginatedList):
    """Schema used to return paginated list of ProjRegConfigs' data to clients."""

    data: Annotated[
        list[ProjRegConfigRead],
        Field(default_factory=list, description="List of projects configurations"),
    ]


class ProjRegConfigQuery(CreationQuery, EditableQuery, PaginationQuery, SortQuery):
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


ProjRegConfigQueryDep = Annotated[ProjRegConfigQuery, Query()]
