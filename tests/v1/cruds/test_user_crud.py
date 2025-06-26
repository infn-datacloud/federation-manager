"""Unit tests for fed_mgr.v1.users.crud.

Tests in this file:
- test_get_user_calls_get_item
- test_get_users_calls_get_items
- test_add_user_calls_add_item
- test_update_user_calls_update_item
- test_delete_user_calls_delete_item
"""

import uuid
from unittest.mock import MagicMock, patch

from fed_mgr.v1.models import User
from fed_mgr.v1.users.crud import (
    add_user,
    delete_user,
    get_user,
    get_users,
    update_user,
)


def test_get_user_found(session):
    """Test get_user returns the User if found."""
    user_id = uuid.uuid4()
    expected_user = MagicMock()
    with patch(
        "fed_mgr.v1.users.crud.get_item", return_value=expected_user
    ) as mock_get_item:
        result = get_user(session=session, user_id=user_id)
        assert result == expected_user
        mock_get_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id
        )


def test_get_user_not_found(session):
    """Test get_user returns None if User not found."""
    user_id = uuid.uuid4()
    with patch("fed_mgr.v1.users.crud.get_item", return_value=None) as mock_get_item:
        result = get_user(session=session, user_id=user_id)
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id
        )


def test_get_users(session):
    """Test get_users calls get_items with correct arguments."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.users.crud.get_items", return_value=(expected_list, expected_count)
    ) as mock_get_items:
        result = get_users(session=session, skip=0, limit=10, sort="name")
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session, entity=User, skip=0, limit=10, sort="name"
        )


def test_add_user_calls_add_item(session):
    """Test add_user calls add_item with correct arguments."""
    user = MagicMock()
    expected_item = MagicMock()
    with patch(
        "fed_mgr.v1.users.crud.add_item", return_value=expected_item
    ) as mock_add_item:
        add_user(session=session, user=user)
        mock_add_item.assert_called_once_with(session=session, entity=User, item=user)


def test_update_user_calls_update_item(session):
    """Test update_user calls update_item with correct arguments."""
    user_id = uuid.uuid4()
    new_user = MagicMock()
    with patch("fed_mgr.v1.users.crud.update_item") as mock_update_item:
        update_user(session=session, user_id=user_id, new_user=new_user)
        mock_update_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id, new_data=new_user
        )


def test_delete_user_calls_delete_item(session):
    """Test delete_user calls delete_item with correct arguments."""
    user_id = uuid.uuid4()
    with patch("fed_mgr.v1.users.crud.delete_item") as mock_delete_item:
        delete_user(session=session, user_id=user_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id
        )
