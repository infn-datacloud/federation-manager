"""DB Models for federation manager v1."""

import uuid
from typing import Annotated

from sqlmodel import Field, Relationship, UniqueConstraint

from fed_mgr.v1.identity_providers.schemas import IdentityProviderBase
from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroupBase
from fed_mgr.v1.identity_providers.user_groups.slas.schemas import SLABase
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


class User(ItemID, CreationTime, UserBase, table=True):
    """Schema used to return User's data to clients."""

    __table_args__ = (
        UniqueConstraint("sub", "issuer", name="unique_sub_issuer_couple"),
    )
