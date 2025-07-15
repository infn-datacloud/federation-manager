"""DB Models for federation manager v1.

Remember: Avoid Annotated when using Relationship
"""

import uuid
from typing import Annotated

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from fed_mgr.v1.identity_providers.schemas import IdentityProviderBase
from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroupBase
from fed_mgr.v1.identity_providers.user_groups.slas.schemas import SLABase
from fed_mgr.v1.locations.schemas import LocationBase
from fed_mgr.v1.providers.identity_providers.schemas import ProviderIdPConnectionBase
from fed_mgr.v1.providers.projects.regions.schemas import ProjRegConfigBase
from fed_mgr.v1.providers.projects.schemas import ProjectBase
from fed_mgr.v1.providers.regions.schemas import RegionBase
from fed_mgr.v1.providers.schemas import ProviderBase, ProviderInternal
from fed_mgr.v1.schemas import CreationTime, ItemID, UpdateTime
from fed_mgr.v1.users.schemas import UserBase


class Administrates(SQLModel, table=True):
    """Association table linking users to providers they administrate."""

    user_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="user.id",
            primary_key=True,
            description="FK pointing to the user's ID",
        ),
    ]
    provider_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="provider.id",
            primary_key=True,
            description="FK pointing to the resource provider's ID",
        ),
    ]


class User(ItemID, CreationTime, UserBase, table=True):
    """Schema used to return User's data to clients."""

    created_locations: list["Location"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "Location.created_by_id"},
    )
    updated_locations: list["Location"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "Location.updated_by_id"},
    )

    created_prov_idp_conns: list["ProviderIdPConnection"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "ProviderIdPConnection.created_by_id"},
    )
    updated_prov_idp_conns: list["ProviderIdPConnection"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "ProviderIdPConnection.updated_by_id"},
    )

    created_idps: list["IdentityProvider"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "IdentityProvider.created_by_id"},
    )
    updated_idps: list["IdentityProvider"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "IdentityProvider.updated_by_id"},
    )

    created_user_groups: list["UserGroup"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "UserGroup.created_by_id"},
    )
    updated_user_groups: list["UserGroup"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "UserGroup.updated_by_id"},
    )

    created_slas: list["SLA"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "SLA.created_by_id"},
    )
    updated_slas: list["SLA"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "SLA.updated_by_id"},
    )

    created_providers: list["Provider"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "Provider.created_by_id"},
    )
    updated_providers: list["Provider"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "Provider.updated_by_id"},
    )

    created_regions: list["Region"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "Region.created_by_id"},
    )
    updated_regions: list["Region"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "Region.updated_by_id"},
    )

    created_projects: list["Project"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "Project.created_by_id"},
    )
    updated_projects: list["Project"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "Project.updated_by_id"},
    )

    created_proj_reg_configs: list["ProjRegConfig"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "ProjRegConfig.created_by_id"},
    )
    updated_proj_reg_configs: list["ProjRegConfig"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "ProjRegConfig.updated_by_id"},
    )

    owned_providers: list["Provider"] = Relationship(
        back_populates="site_admins", link_model=Administrates
    )

    __table_args__ = (
        UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
    )


class Location(ItemID, CreationTime, UpdateTime, LocationBase, table=True):
    """Physical site hosting one or multiple resource providers.

    Avoid deletion if there is at least one linked region.
    """

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_locations",
        sa_relationship_kwargs={"foreign_keys": "Location.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_locations",
        sa_relationship_kwargs={"foreign_keys": "Location.updated_by_id"},
    )

    regions: list["Region"] = Relationship(
        back_populates="location", passive_deletes="all"
    )


class ProviderIdPConnection(
    CreationTime, UpdateTime, ProviderIdPConnectionBase, table=True
):
    """Association table linking providers to trusted identity providers."""

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_prov_idp_conns",
        sa_relationship_kwargs={"foreign_keys": "ProviderIdPConnection.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_prov_idp_conns",
        sa_relationship_kwargs={"foreign_keys": "ProviderIdPConnection.updated_by_id"},
    )

    idp_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="identityprovider.id",
            primary_key=True,
            description="FK pointing to the identity provider's ID",
        ),
    ]
    idp: "IdentityProvider" = Relationship(back_populates="linked_providers")

    provider_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="provider.id",
            primary_key=True,
            description="FK pointing to the resource provider's ID",
        ),
    ]
    provider: "Provider" = Relationship(back_populates="idps")


class IdentityProvider(
    ItemID, CreationTime, UpdateTime, IdentityProviderBase, table=True
):
    """Schema used to return Identity Provider's data to clients.

    Avoid deletion if there is at least one linked user group or one linked resource
    provider.
    """

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_idps",
        sa_relationship_kwargs={"foreign_keys": "IdentityProvider.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_idps",
        sa_relationship_kwargs={"foreign_keys": "IdentityProvider.updated_by_id"},
    )

    linked_providers: list[ProviderIdPConnection] = Relationship(
        back_populates="idp", passive_deletes="all"
    )
    user_groups: list["UserGroup"] = Relationship(
        back_populates="idp", passive_deletes="all"
    )


class UserGroup(ItemID, CreationTime, UpdateTime, UserGroupBase, table=True):
    """Schema used to return User Group's data to clients.

    Avoid deletion if there is at least one linked SLA.
    """

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_user_groups",
        sa_relationship_kwargs={"foreign_keys": "UserGroup.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_user_groups",
        sa_relationship_kwargs={"foreign_keys": "UserGroup.updated_by_id"},
    )

    idp_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="identityprovider.id",
            ondelete="RESTRICT",  # Avoid on cascade deletion
            description="Parent user group",
        ),
    ]
    idp: IdentityProvider = Relationship(back_populates="user_groups")

    slas: list["SLA"] = Relationship(back_populates="user_group", passive_deletes="all")


class SLA(ItemID, CreationTime, UpdateTime, SLABase, table=True):
    """Schema used to return SLA's data to clients."""

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_slas",
        sa_relationship_kwargs={"foreign_keys": "SLA.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_slas",
        sa_relationship_kwargs={"foreign_keys": "SLA.updated_by_id"},
    )

    user_group_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="usergroup.id",
            ondelete="RESTRICT",  # Avoid on cascade deletion
            description="Parent user group",
        ),
    ]
    user_group: UserGroup = Relationship(back_populates="slas")


class Provider(
    ItemID, CreationTime, UpdateTime, ProviderBase, ProviderInternal, table=True
):
    """Schema used to return Provider's data to clients.

    Avoid deletion if there is at least one linked user group.
    On cascade, delete the connection with the identity providers.
    """

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_providers",
        sa_relationship_kwargs={"foreign_keys": "Provider.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_providers",
        sa_relationship_kwargs={"foreign_keys": "Provider.updated_by_id"},
    )

    site_admins: list[User] = Relationship(
        back_populates="owned_providers", link_model=Administrates
    )
    idps: list[ProviderIdPConnection] = Relationship(
        back_populates="provider", cascade_delete=True
    )
    regions: list["Region"] = Relationship(
        back_populates="provider", passive_deletes="all"
    )
    projects: list["Project"] = Relationship(
        back_populates="provider", passive_deletes="all"
    )


class ProjRegConfig(CreationTime, UpdateTime, ProjRegConfigBase, table=True):
    """Association table linking projects to regions."""

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_proj_reg_configs",
        sa_relationship_kwargs={"foreign_keys": "ProjRegConfig.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_proj_reg_configs",
        sa_relationship_kwargs={"foreign_keys": "ProjRegConfig.updated_by_id"},
    )

    region_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="region.id",
            primary_key=True,
            description="FK pointing to the region's ID",
        ),
    ]
    region: "Region" = Relationship(back_populates="linked_projects")

    project_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="project.id",
            primary_key=True,
            description="FK pointing to the project's ID",
        ),
    ]
    project: "Project" = Relationship(back_populates="regions")


class Region(ItemID, CreationTime, UpdateTime, RegionBase, table=True):
    """Schema used to return Region's data to clients."""

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_regions",
        sa_relationship_kwargs={"foreign_keys": "Region.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_regions",
        sa_relationship_kwargs={"foreign_keys": "Region.updated_by_id"},
    )

    provider_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="provider.id",
            ondelete="RESTRICT",  # Avoid on cascade deletion
            description="Parent provider",
        ),
    ]
    provider: Provider = Relationship(back_populates="regions")

    location_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="location.id",
            ondelete="RESTRICT",  # Avoid on cascade deletion
            description="Parent location",
        ),
    ]
    location: Location = Relationship(back_populates="regions")

    linked_projects: list[ProjRegConfig] = Relationship(
        back_populates="region", passive_deletes="all"
    )


class Project(ItemID, CreationTime, UpdateTime, ProjectBase, table=True):
    """Schema used to return Project's data to clients."""

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_projects",
        sa_relationship_kwargs={"foreign_keys": "Project.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_projects",
        sa_relationship_kwargs={"foreign_keys": "Project.updated_by_id"},
    )

    provider_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="provider.id",
            ondelete="RESTRICT",  # Avoid on cascade deletion
            description="Parent provider",
        ),
    ]
    provider: Provider = Relationship(back_populates="projects")

    regions: list[ProjRegConfig] = Relationship(
        back_populates="project", cascade_delete=True
    )
