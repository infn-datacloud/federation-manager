"""Unit tests for fed_mgr.v1.identity_providers.user_groups.crud.

Tests in this file:
- test_get_user_group_calls_get_item
- test_get_user_groups_calls_get_items
- test_add_user_group_calls_add_item
- test_update_user_group_calls_update_item
- test_delete_user_group_calls_delete_item
"""

import uuid
from unittest import mock

from fed_mgr.v1.identity_providers.schemas import IdentityProvider
from fed_mgr.v1.identity_providers.user_groups.crud import (
    add_user_group,
    delete_user_group,
    get_user_group,
    get_user_groups,
    update_user_group,
)
from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroup, UserGroupCreate
from fed_mgr.v1.users.schemas import User


def test_get_user_group_calls_get_item(session):
    """Test get_user_group calls get_item with correct arguments."""
    user_group_id = uuid.uuid4()
    with mock.patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.get_item"
    ) as mock_get_item:
        get_user_group(user_group_id=user_group_id, session=session)
        mock_get_item.assert_called_once_with(
            session=session, entity=UserGroup, item_id=user_group_id
        )


def test_get_user_groups_calls_get_items(session):
    """Test get_user_groups calls get_items with correct arguments."""
    with mock.patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.get_items"
    ) as mock_get_items:
        get_user_groups(session=session, skip=0, limit=10, sort="name")
        mock_get_items.assert_called_once_with(
            session=session, entity=UserGroup, skip=0, limit=10, sort="name"
        )


def test_add_user_group_calls_add_item(session):
    """Test add_user_group calls add_item with correct arguments."""
    fake_user_group = mock.Mock(spec=UserGroupCreate)
    fake_user = mock.Mock(spec=User)
    fake_idp = mock.Mock(spec=IdentityProvider)
    fake_user.id = uuid.uuid4()
    fake_idp.id = uuid.uuid4()
    with mock.patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.add_item"
    ) as mock_add_item:
        add_user_group(
            session=session,
            user_group=fake_user_group,
            created_by=fake_user,
            parent_idp=fake_idp,
        )
        mock_add_item.assert_called_once_with(
            session=session,
            entity=UserGroup,
            item=fake_user_group,
            created_by=fake_user.id,
            updated_by=fake_user.id,
            idp=fake_idp.id,
        )


def test_update_user_group_calls_update_item(session):
    """Test update_user_group calls update_item with correct arguments."""
    user_group_id = uuid.uuid4()
    fake_user_group = mock.Mock(spec=UserGroupCreate)
    fake_user = mock.Mock(spec=User)
    fake_user.id = uuid.uuid4()
    with mock.patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.update_item"
    ) as mock_update_item:
        update_user_group(
            session=session,
            user_group_id=user_group_id,
            new_user_group=fake_user_group,
            updated_by=fake_user,
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=UserGroup,
            item_id=user_group_id,
            new_data=fake_user_group,
            updated_by=fake_user.id,
        )


def test_delete_user_group_calls_delete_item(session):
    """Test delete_user_group calls delete_item with correct arguments."""
    user_group_id = uuid.uuid4()
    with mock.patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.delete_item"
    ) as mock_delete_item:
        delete_user_group(session=session, user_group_id=user_group_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=UserGroup, item_id=user_group_id
        )
