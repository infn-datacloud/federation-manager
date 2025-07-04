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
from fed_mgr.v1.providers.schemas import ProviderBase, ProviderInternal
from fed_mgr.v1.schemas import Creation, CreationTime, Editable, ItemID
from fed_mgr.v1.users.schemas import UserBase


class Location(ItemID, Creation, Editable, LocationBase, table=True):
    """Physical site hosting one or multiple resource providers."""


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
    provider_id: Annotated[
        uuid.UUID,
        Field(
            foreign_key="provider.id",
            primary_key=True,
            description="FK pointing to the resource provider's ID",
        ),
    ]
    idp: "IdentityProvider" = Relationship(back_populates="linked_providers")
    provider: "Provider" = Relationship(back_populates="idps")


class IdentityProvider(ItemID, Creation, Editable, IdentityProviderBase, table=True):
    """Schema used to return Identity Provider's data to clients."""

    linked_providers: list[ProviderIdPConnection] = Relationship(back_populates="idp")


class UserGroup(ItemID, Creation, Editable, UserGroupBase, table=True):
    """Schema used to return User Group's data to clients."""

    idp_id: Annotated[
        uuid.UUID,
        Field(foreign_key="identityprovider.id", description="Parent user group"),
    ]


class SLA(ItemID, Creation, Editable, SLABase, table=True):
    """Schema used to return SLA's data to clients."""

    user_group_id: Annotated[
        uuid.UUID,
        Field(foreign_key="usergroup.id", description="Parent user group"),
    ]


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
    """Schema used to return Provider's data to clients."""

    site_admins: list[User] = Relationship(
        back_populates="owned_providers", link_model=Administrates
    )
    idps: list[ProviderIdPConnection] = Relationship(back_populates="provider")
