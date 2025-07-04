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
from fed_mgr.v1.providers.regions.schemas import RegionBase
from fed_mgr.v1.providers.schemas import ProviderBase, ProviderInternal
from fed_mgr.v1.schemas import Creation, CreationTime, Editable, ItemID
from fed_mgr.v1.users.schemas import UserBase


class Location(ItemID, Creation, Editable, LocationBase, table=True):
    """Physical site hosting one or multiple resource providers.

    Avoid deletion if there is at least one linked region.
    """

    regions: list["Region"] = Relationship(
        back_populates="location", passive_deletes="all"
    )


class ProviderIdPConnection(Creation, Editable, ProviderIdPConnectionBase, table=True):
    """Association table linking users to providers they administrate."""

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


class IdentityProvider(ItemID, Creation, Editable, IdentityProviderBase, table=True):
    """Schema used to return Identity Provider's data to clients.

    Avoid deletion if there is at least one linked user group or one linked resource
    provider.
    """

    linked_providers: list[ProviderIdPConnection] = Relationship(
        back_populates="idp", passive_deletes="all"
    )
    user_groups: list["UserGroup"] = Relationship(
        back_populates="idp", passive_deletes="all"
    )


class UserGroup(ItemID, Creation, Editable, UserGroupBase, table=True):
    """Schema used to return User Group's data to clients.

    Avoid deletion if there is at least one linked SLA.
    """

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


class SLA(ItemID, Creation, Editable, SLABase, table=True):
    """Schema used to return SLA's data to clients."""

    user_group_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="usergroup.id",
            ondelete="RESTRICT",  # Avoid on cascade deletion
            description="Parent user group",
        ),
    ]
    user_group: UserGroup = Relationship(back_populates="slas")


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

    owned_providers: list["Provider"] = Relationship(
        back_populates="site_admins", link_model=Administrates
    )

    __table_args__ = (
        UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
    )


class Provider(ItemID, Creation, Editable, ProviderBase, ProviderInternal, table=True):
    """Schema used to return Provider's data to clients.

    Avoid deletion if there is at least one linked user group.
    On cascade, delete the connection with the identity providers.
    """

    site_admins: list[User] = Relationship(
        back_populates="owned_providers", link_model=Administrates
    )
    idps: list[ProviderIdPConnection] = Relationship(
        back_populates="provider", cascade_delete=True
    )
    regions: list["Region"] = Relationship(
        back_populates="provider", passive_deletes="all"
    )


class Region(ItemID, Creation, Editable, RegionBase, table=True):
    """Schema used to return Region's data to clients."""

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
