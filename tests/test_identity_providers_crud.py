"""Unit tests for fed_mgr.v1.identity_providers.crud.

Tests in this file:
- test_get_idp_calls_get_item
- test_get_idps_calls_get_items
- test_add_idp_calls_add_item
- test_update_idp_calls_update_item
- test_delete_idp_calls_delete_item
"""

import uuid
from unittest import mock

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


def test_get_idp_calls_get_item(session):
    """Test get_idp calls get_item with correct arguments."""
    idp_id = uuid.uuid4()
    with mock.patch("fed_mgr.v1.identity_providers.crud.get_item") as mock_get_item:
        get_idp(idp_id=idp_id, session=session)
        mock_get_item.assert_called_once_with(
            session=session, entity=IdentityProvider, item_id=idp_id
        )


def test_get_idps_calls_get_items(session):
    """Test get_idps calls get_items with correct arguments."""
    with mock.patch("fed_mgr.v1.identity_providers.crud.get_items") as mock_get_items:
        get_idps(session=session, skip=0, limit=10, sort="name")
        mock_get_items.assert_called_once_with(
            session=session, entity=IdentityProvider, skip=0, limit=10, sort="name"
        )


def test_add_idp_calls_add_item(session):
    """Test add_idp calls add_item with correct arguments."""
    fake_idp = mock.Mock(spec=IdentityProviderCreate)
    fake_user = mock.Mock(spec=User)
    with mock.patch("fed_mgr.v1.identity_providers.crud.add_item") as mock_add_item:
        add_idp(session=session, idp=fake_idp, created_by=fake_user)
        mock_add_item.assert_called_once_with(
            session=session,
            entity=IdentityProvider,
            item=fake_idp,
            created_by=fake_user.id,
            updated_by=fake_user.id,
        )


def test_update_idp_calls_update_item(session):
    """Test update_idp calls update_item with correct arguments."""
    idp_id = uuid.uuid4()
    fake_idp = mock.Mock(spec=IdentityProviderCreate)
    fake_user = mock.Mock(spec=User)
    with mock.patch(
        "fed_mgr.v1.identity_providers.crud.update_item"
    ) as mock_update_item:
        update_idp(
            session=session, idp_id=idp_id, new_idp=fake_idp, updated_by=fake_user
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=IdentityProvider,
            item_id=idp_id,
            new_data=fake_idp,
            updated_by=fake_user.id,
        )


def test_delete_idp_calls_delete_item(session):
    """Test delete_idp calls delete_item with correct arguments."""
    idp_id = uuid.uuid4()
    with mock.patch(
        "fed_mgr.v1.identity_providers.crud.delete_item"
    ) as mock_delete_item:
        delete_idp(session=session, idp_id=idp_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=IdentityProvider, item_id=idp_id
        )
