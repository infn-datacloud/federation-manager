"""DB Models for federation manager v1.

Remember: Avoid Annotated when using Relationship
"""

import uuid
from typing import Annotated, Optional

from pydantic import computed_field
from sqlalchemy.ext.declarative import declared_attr
from sqlmodel import (
    Column,
    Computed,
    Field,
    Index,
    Relationship,
    SQLModel,
    String,
    UniqueConstraint,
    true,
)

from fed_mgr.db import engine
from fed_mgr.v1.identity_providers.schemas import IdentityProviderBase
from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroupBase
from fed_mgr.v1.identity_providers.user_groups.slas.schemas import SLABase
from fed_mgr.v1.providers.identity_providers.schemas import IdpOverridesBase
from fed_mgr.v1.providers.projects.regions.schemas import RegionOverridesBase
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
            ondelete="CASCADE",
            description="FK pointing to the resource provider's ID",
        ),
    ]


class Evaluates(SQLModel, table=True):
    """Association table linking users to providers they evaulates."""

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
            ondelete="CASCADE",
            description="FK pointing to the resource provider's ID",
        ),
    ]


class User(ItemID, CreationTime, UserBase, table=True):
    """Schema used to return User's data to clients."""

    # created_locations: list["Location"] = Relationship(
    #     back_populates="created_by",
    #     sa_relationship_kwargs={"foreign_keys": "Location.created_by_id"},
    # )
    # updated_locations: list["Location"] = Relationship(
    #     back_populates="updated_by",
    #     sa_relationship_kwargs={"foreign_keys": "Location.updated_by_id"},
    # )

    created_prov_idp_conns: list["IdpOverrides"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "IdpOverrides.created_by_id"},
    )
    updated_prov_idp_conns: list["IdpOverrides"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "IdpOverrides.updated_by_id"},
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

    created_proj_reg_configs: list["RegionOverrides"] = Relationship(
        back_populates="created_by",
        sa_relationship_kwargs={"foreign_keys": "RegionOverrides.created_by_id"},
    )
    updated_proj_reg_configs: list["RegionOverrides"] = Relationship(
        back_populates="updated_by",
        sa_relationship_kwargs={"foreign_keys": "RegionOverrides.updated_by_id"},
    )

    owned_providers: list["Provider"] = Relationship(
        back_populates="site_admins", link_model=Administrates
    )
    assigned_providers: list["Provider"] = Relationship(
        back_populates="site_testers", link_model=Evaluates
    )

    __table_args__ = (
        UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
    )
    __hash__ = object.__hash__


# class Location(ItemID, CreationTime, UpdateTime, LocationBase, table=True):
#     """Physical site hosting one or multiple resource providers.

#     Avoid deletion if there is at least one linked region.
#     """

#     created_by_id: Annotated[
#         uuid.UUID,
#         Field(foreign_key="user.id", description="User who created this item."),
#     ]
#     created_by: User = Relationship(
#         back_populates="created_locations",
#         sa_relationship_kwargs={"foreign_keys": "Location.created_by_id"},
#     )

#     updated_by_id: Annotated[
#         uuid.UUID,
#         Field(foreign_key="user.id", description="User who last updated this item."),
#     ]
#     updated_by: User = Relationship(
#         back_populates="updated_locations",
#         sa_relationship_kwargs={"foreign_keys": "Location.updated_by_id"},
#     )

#     regions: list["Region"] = Relationship(
#         back_populates="location", passive_deletes="all"
#     )


class IdpOverrides(CreationTime, UpdateTime, IdpOverridesBase, table=True):
    """Association table linking providers to trusted identity providers."""

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_prov_idp_conns",
        sa_relationship_kwargs={"foreign_keys": "IdpOverrides.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_prov_idp_conns",
        sa_relationship_kwargs={"foreign_keys": "IdpOverrides.updated_by_id"},
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
            ondelete="CASCADE",
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

    linked_providers: list[IdpOverrides] = Relationship(
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

    __table_args__ = (
        UniqueConstraint("name", "idp_id", name="unique_name_idp_couple"),
    )


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

    projects: list["Project"] = Relationship(
        back_populates="sla", passive_deletes="all"
    )


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
    site_testers: list[User] = Relationship(
        back_populates="assigned_providers", link_model=Evaluates
    )
    idps: list[IdpOverrides] = Relationship(
        back_populates="provider", cascade_delete=True
    )
    regions: list["Region"] = Relationship(
        back_populates="provider", passive_deletes="all"
    )
    projects: list["Project"] = Relationship(
        back_populates="provider", passive_deletes="all"
    )

    @computed_field
    @property
    def root_project(self) -> Optional["Project"]:
        """Return the root project from the list of associated projects.

        Iterates through the `projects` attribute and returns the first project
        where `is_root` is True. If no such project exists, returns None.

        Returns:
            Project | None: The root project if found, otherwise None.

        """
        return next(filter(lambda x: x.is_root, self.projects), None)


class RegionOverrides(CreationTime, UpdateTime, RegionOverridesBase, table=True):
    """Association table linking projects to regions."""

    created_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who created this item."),
    ]
    created_by: User = Relationship(
        back_populates="created_proj_reg_configs",
        sa_relationship_kwargs={"foreign_keys": "RegionOverrides.created_by_id"},
    )

    updated_by_id: Annotated[
        uuid.UUID,
        Field(foreign_key="user.id", description="User who last updated this item."),
    ]
    updated_by: User = Relationship(
        back_populates="updated_proj_reg_configs",
        sa_relationship_kwargs={"foreign_keys": "RegionOverrides.updated_by_id"},
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
            ondelete="CASCADE",
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

    # location_id: Annotated[
    #     uuid.UUID,
    #     Field(
    #         foreign_key="location.id",
    #         ondelete="RESTRICT",  # Avoid on cascade deletion
    #         description="Parent location",
    #     ),
    # ]
    # location: Location = Relationship(back_populates="regions")

    linked_projects: list[RegionOverrides] = Relationship(
        back_populates="region", passive_deletes="all"
    )

    __table_args__ = (
        UniqueConstraint("name", "provider_id", name="unique_name_provider_couple"),
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

    sla_id: Annotated[
        uuid.UUID | None,
        Field(
            foreign_key="sla.id",
            ondelete="RESTRICT",  # Avoid on cascade deletion
            description="Linked SLA",
        ),
    ]
    sla: SLA = Relationship(back_populates="projects")

    regions: list[RegionOverrides] = Relationship(
        back_populates="project", cascade_delete=True
    )

    if engine.dialect.name == "mysql":
        provider_root_id: Annotated[
            int | None,
            Field(
                sa_column=Column(
                    "provider_root_id",
                    String(32),  # UUID length
                    Computed("IF(is_root = TRUE, provider_id, NULL)", persisted=True),
                )
            ),
        ]

        __table_args__ = (
            UniqueConstraint(
                "iaas_project_id", "provider_id", name="unique_projid_provider_couple"
            ),
            Index("ix_unique_provider_root", "provider_root_id", unique=True),
        )

    elif engine.dialect.name == "sqlite":

        @declared_attr
        def __table_args__(self):
            """Return table arguments for the Project model when using SQLite."""
            return (
                UniqueConstraint(
                    "iaas_project_id",
                    "provider_id",
                    name="unique_projid_provider_couple",
                ),
                Index(
                    "ix_unique_provider_root",
                    "provider_id",
                    unique=True,
                    sqlite_where=(self.is_root == true()),
                ),
            )
