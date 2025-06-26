"""DB Models for federation manager v1."""

import uuid
from typing import Annotated

from sqlmodel import AutoString, Field, Relationship, SQLModel, UniqueConstraint

from fed_mgr.v1.identity_providers.schemas import IdentityProviderBase
from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroupBase
from fed_mgr.v1.identity_providers.user_groups.slas.schemas import SLABase
from fed_mgr.v1.providers.schemas import ProviderBase, ProviderInternal
from fed_mgr.v1.schemas import Creation, CreationTime, Editable, ItemID
from fed_mgr.v1.users.schemas import UserBase


class IdentityProvider(ItemID, Creation, Editable, IdentityProviderBase, table=True):
    """Schema used to return Identity Provider's data to clients."""


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

    owned_providers: Annotated[
        list["Provider"],
        Field(
            default_factory=list,
            sa_type=AutoString,
            description="List of the resource providers administrated by this user",
        ),
        Relationship(back_populates="site_admins", link_model=Administrates),
    ]

    __table_args__ = (
        UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
    )


class Provider(ItemID, Creation, Editable, ProviderBase, ProviderInternal, table=True):
    """Schema used to return Provider's data to clients."""

    site_admins: Annotated[
        list[User],
        Field(
            sa_type=AutoString, description="List of the provider/site administrators"
        ),
        Relationship(back_populates="owned_providers", link_model=Administrates),
    ]
