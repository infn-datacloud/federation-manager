"""Tests for the UserGroup model, including field validation, uniqueness constraints."""

import uuid
from datetime import datetime

import pytest
import sqlalchemy.exc
from sqlmodel import Session

from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroupBase
from fed_mgr.v1.models import IdentityProvider, User, UserGroup
from fed_mgr.v1.schemas import CreationTime, ItemID, UpdateTime


def test_user_group_model(
    db_session: Session, user_model: User, idp_model: IdentityProvider
) -> None:
    """Verify UserGroup model fields, types and relationships.

    The test creates a `UserGroup` attached to `idp_model`, persists it and
    asserts that mixins, typed fields, and relationships are correctly set.
    """
    desc = "desc"
    name = "Test Group"
    group = UserGroup(
        created_by=user_model,
        updated_by=user_model,
        name=name,
        description=desc,
        idp=idp_model,
    )
    db_session.add(group)
    db_session.commit()

    assert isinstance(group, ItemID)
    assert isinstance(group, CreationTime)
    assert isinstance(group, UpdateTime)
    assert isinstance(group, UserGroupBase)
    assert isinstance(group.id, uuid.UUID)
    assert isinstance(group.created_at, datetime)
    assert isinstance(group.updated_at, datetime)
    assert group.created_by == user_model
    assert group.created_by_id == user_model.id
    assert group.updated_by == user_model
    assert group.updated_by_id == user_model.id
    assert group.name == name
    assert group.description == desc
    assert group.idp == idp_model
    assert group.idp_id == idp_model.id
    assert group.slas == []

    assert user_model.created_user_groups == [group]
    assert user_model.updated_user_groups == [group]


def test_duplicate_user_group(
    db_session: Session,
    user_model: User,
    idp_model: IdentityProvider,
    user_group_model: UserGroup,
) -> None:
    """Ensure unique constraint prevents duplicate group names per IDP.

    Creating a second UserGroup with the same name under the same identity
    provider should raise an IntegrityError on commit.
    """
    user = UserGroup(
        created_by=user_model,
        updated_by=user_model,
        name=user_group_model.name,
        idp=idp_model,
    )
    db_session.add(user)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match="UNIQUE constraint failed: usergroup.name, usergroup.idp_id",
    ):
        db_session.commit()


def test_same_user_group_different_idp(
    db_session: Session, user_model: User, user_group_model: UserGroup
) -> None:
    """Verify identical group names are allowed under different IDPs.

    This test creates a new IdentityProvider and then a UserGroup using the
    same name as `user_group_model`. It should succeed because the unique
    constraint is scoped to the identity provider.
    """
    idp = IdentityProvider(
        created_by=user_model,
        updated_by=user_model,
        endpoint="https://another.issuer.com",
        name="Another IDP",
        groups_claim="groups",
    )
    user_group = UserGroup(
        created_by=user_model,
        updated_by=user_model,
        name=user_group_model.name,
        idp=idp,
    )
    db_session.add(user_group)
    db_session.commit()

    assert user_group.id is not None
    assert user_group.id != user_group_model.id
