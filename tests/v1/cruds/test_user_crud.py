"""Unit tests for fed_mgr.v1.users.crud.

Tests in this file:
- test_get_user_calls_get_item
- test_get_users_calls_get_items
- test_add_user_calls_add_item
- test_update_user_calls_update_item
- test_delete_user_calls_delete_item
"""

import uuid
from unittest import mock

from fed_mgr.v1.users.crud import (
    add_user,
    delete_user,
    get_user,
    get_users,
    update_user,
)
from fed_mgr.v1.users.schemas import User, UserCreate


def test_get_user_calls_get_item(session):
    """Test get_user calls get_item with correct arguments."""
    user_id = uuid.uuid4()
    with mock.patch("fed_mgr.v1.users.crud.get_item") as mock_get_item:
        get_user(user_id=user_id, session=session)
        mock_get_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id
        )


def test_get_users_calls_get_items(session):
    """Test get_users calls get_items with correct arguments."""
    with mock.patch("fed_mgr.v1.users.crud.get_items") as mock_get_items:
        get_users(session=session, skip=0, limit=10, sort="name")
        mock_get_items.assert_called_once_with(
            session=session, entity=User, skip=0, limit=10, sort="name"
        )


def test_add_user_calls_add_item(session):
    """Test add_user calls add_item with correct arguments."""
    fake_user = mock.Mock(spec=UserCreate)
    with mock.patch("fed_mgr.v1.users.crud.add_item") as mock_add_item:
        add_user(session=session, user=fake_user)
        mock_add_item.assert_called_once_with(
            session=session, entity=User, item=fake_user
        )


def test_update_user_calls_update_item(session):
    """Test update_user calls update_item with correct arguments."""
    user_id = uuid.uuid4()
    fake_user = mock.Mock(spec=UserCreate)
    with mock.patch("fed_mgr.v1.users.crud.update_item") as mock_update_item:
        update_user(session=session, user_id=user_id, new_user=fake_user)
        mock_update_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id, new_data=fake_user
        )


def test_delete_user_calls_delete_item(session):
    """Test delete_user calls delete_item with correct arguments."""
    user_id = uuid.uuid4()
    with mock.patch("fed_mgr.v1.users.crud.delete_item") as mock_delete_item:
        delete_user(session=session, user_id=user_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id
        )


