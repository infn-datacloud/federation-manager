"""Unit tests for fed_mgr.v1.identity_providers.user_groups.crud.

Tests in this file:
- test_get_user_group_calls_get_item
- test_get_user_groups_calls_get_items
- test_add_user_group_calls_add_item
- test_update_user_group_calls_update_item
- test_delete_user_group_calls_delete_item
"""

import uuid
from unittest.mock import MagicMock, patch

from fed_mgr.v1.identity_providers.user_groups.crud import (
    add_user_group,
    delete_user_group,
    get_user_group,
    get_user_groups,
    update_user_group,
)
from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroup


def test_get_user_group_found(session):
    """Test get_user_group returns the UserGroup if found."""
    user_group_id = uuid.uuid4()
    expected_user_group = MagicMock()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.get_item",
        return_value=expected_user_group,
    ) as mock_get_item:
        result = get_user_group(session=session, user_group_id=user_group_id)
        assert result == expected_user_group
        mock_get_item.assert_called_once_with(
            session=session, entity=UserGroup, item_id=user_group_id
        )


def test_get_user_group_not_found(session):
    """Test get_user_group returns None if UserGroup not found."""
    user_group_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_user_group(session=session, user_group_id=user_group_id)
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session, entity=UserGroup, item_id=user_group_id
        )


def test_get_user_groups(session):
    """Test get_user_groups calls get_items with correct arguments."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_user_groups(session=session, skip=0, limit=10, sort="name")
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session, entity=UserGroup, skip=0, limit=10, sort="name"
        )


def test_add_user_group(session):
    """Test add_user_group calls add_item with correct arguments."""
    user_group = MagicMock()
    created_by = MagicMock()
    created_by.id = uuid.uuid4()
    parent_idp = MagicMock()
    parent_idp.id = uuid.uuid4()
    expected_item = MagicMock()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.add_item",
        return_value=expected_item,
    ) as mock_add_item:
        result = add_user_group(
            session=session,
            user_group=user_group,
            created_by=created_by,
            parent_idp=parent_idp,
        )
        assert result == expected_item
        mock_add_item.assert_called_once_with(
            session=session,
            entity=UserGroup,
            item=user_group,
            created_by=created_by.id,
            updated_by=created_by.id,
            idp=parent_idp.id,
        )


def test_update_user_group(session):
    """Test update_user_group calls update_item with correct arguments."""
    user_group_id = uuid.uuid4()
    new_user_group = MagicMock()
    updated_by = MagicMock()
    updated_by.id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.update_item"
    ) as mock_update_item:
        update_user_group(
            session=session,
            user_group_id=user_group_id,
            new_user_group=new_user_group,
            updated_by=updated_by,
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=UserGroup,
            item_id=user_group_id,
            new_data=new_user_group,
            updated_by=updated_by.id,
        )


def test_delete_user_group_calls_delete_item(session):
    """Test delete_user_group calls delete_item with correct arguments."""
    user_group_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.crud.delete_item"
    ) as mock_delete_item:
        delete_user_group(session=session, user_group_id=user_group_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=UserGroup, item_id=user_group_id
        )
