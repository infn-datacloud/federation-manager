"""Unit tests for fed_mgr.v1.identity_providers.crud.

Tests in this file:
- test_get_idp_calls_get_item
- test_get_idps_calls_get_items
- test_add_idp_calls_add_item
- test_update_idp_calls_update_item
- test_delete_idp_calls_delete_item
"""

import uuid
from unittest.mock import MagicMock, patch

from fed_mgr.v1.identity_providers.crud import (
    add_idp,
    delete_idp,
    get_idp,
    get_idps,
    update_idp,
)
from fed_mgr.v1.identity_providers.schemas import (
    IdentityProvider,
    IdentityProviderCreate,
)
from fed_mgr.v1.users.schemas import User


def test_get_idp_found(session):
    """Test get_idp returns the IdentityProvider if found."""
    idp_id = uuid.uuid4()
    expected_idp = MagicMock()
    with patch(
        "fed_mgr.v1.identity_providers.crud.get_item",
        return_value=expected_idp,
    ) as mock_get_item:
        result = get_idp(session=session, idp_id=idp_id)
        assert result == expected_idp
        mock_get_item.assert_called_once_with(
            session=session, entity=IdentityProvider, item_id=idp_id
        )


def test_get_idp_not_found(session):
    """Test get_idp returns None if IdentityProvider not found."""
    idp_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_idp(session=session, idp_id=idp_id)
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session, entity=IdentityProvider, item_id=idp_id
        )


def test_get_idps(session):
    """Test get_idps calls get_items with correct arguments."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.identity_providers.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_idps(session=session, skip=0, limit=10, sort="name")
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session, entity=IdentityProvider, skip=0, limit=10, sort="name"
        )


def test_add_idp_calls_add_item(session):
    """Test add_idp calls add_item with correct arguments."""
    idp = MagicMock()
    created_by = MagicMock()
    created_by.id = uuid.uuid4()
    expected_item = MagicMock()
    with patch(
        "fed_mgr.v1.identity_providers.crud.add_item",
        return_value=expected_item,
    ) as mock_add_item:
        result = add_idp(session=session, idp=idp, created_by=created_by)
        assert result == expected_item
        mock_add_item.assert_called_once_with(
            session=session,
            entity=IdentityProvider,
            item=idp,
            created_by=created_by.id,
            updated_by=created_by.id,
        )


def test_update_idp_calls_update_item(session):
    """Test update_idp calls update_item with correct arguments."""
    idp_id = uuid.uuid4()
    new_idp = MagicMock(spec=IdentityProviderCreate)
    updated_by = MagicMock(spec=User)
    updated_by.id = uuid.uuid4()
    with patch("fed_mgr.v1.identity_providers.crud.update_item") as mock_update_item:
        update_idp(
            session=session, idp_id=idp_id, new_idp=new_idp, updated_by=updated_by
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=IdentityProvider,
            item_id=idp_id,
            new_data=new_idp,
            updated_by=updated_by.id,
        )


def test_delete_idp_calls_delete_item(session):
    """Test delete_idp calls delete_item with correct arguments."""
    idp_id = uuid.uuid4()
    with patch("fed_mgr.v1.identity_providers.crud.delete_item") as mock_delete_item:
        delete_idp(session=session, idp_id=idp_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=IdentityProvider, item_id=idp_id
        )
