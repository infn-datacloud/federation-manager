"""Unit tests for fed_mgr.v1.providers.identity_providers.crud.

Tests in this file:
- test_get_provider_idp_rel_calls_get_item
- test_get_provider_idp_rels_calls_get_items
- test_add_provider_idp_rel_calls_add_item
- test_update_provider_idp_rel_calls_update_item
- test_delete_provider_idp_rel_calls_delete_item
"""

import uuid
from unittest.mock import MagicMock, patch

from fed_mgr.v1.models import IdpOverrides
from fed_mgr.v1.providers.identity_providers.crud import (
    connect_prov_idp,
    disconnect_prov_idp,
    get_idp_overrides,
    get_idp_overrides_list,
    update_idp_overrides,
)


def test_get_prov_idp_rel_found(session):
    """Test get_idp_overrides returns the Provider-IdP relationship if found."""
    idp_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    expected_idp = MagicMock()
    with patch(
        "fed_mgr.v1.providers.identity_providers.crud.get_item",
        return_value=expected_idp,
    ) as mock_get_item:
        result = get_idp_overrides(
            session=session, idp_id=idp_id, provider_id=provider_id
        )
        assert result == expected_idp
        mock_get_item.assert_called_once_with(
            session=session,
            entity=IdpOverrides,
            idp_id=idp_id,
            provider_id=provider_id,
        )


def test_get_idp_not_found(session):
    """Test get_idp_overrides returns None if Provider-IdP relationship not found."""
    idp_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.identity_providers.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_idp_overrides(
            session=session, idp_id=idp_id, provider_id=provider_id
        )
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session,
            entity=IdpOverrides,
            idp_id=idp_id,
            provider_id=provider_id,
        )


def test_get_idps(session):
    """Test get_idp_overrides_list calls get_items with correct arguments."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.providers.identity_providers.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_idp_overrides_list(session=session, skip=0, limit=10, sort="name")
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session, entity=IdpOverrides, skip=0, limit=10, sort="name"
        )


def test_add_idp_calls_add_item(session):
    """Test connect_prov_idp calls add_item with correct arguments."""
    config = MagicMock()
    idp = MagicMock()
    provider = MagicMock()
    created_by = MagicMock()
    expected_item = MagicMock()
    with (
        patch(
            "fed_mgr.v1.providers.identity_providers.crud.add_item",
            return_value=expected_item,
        ) as mock_add_item,
        patch(
            "fed_mgr.v1.providers.identity_providers.crud.get_idp", return_value=idp
        ) as mock_get_idp,
    ):
        result = connect_prov_idp(
            session=session,
            config=config,
            provider=provider,
            created_by=created_by,
        )
        assert result == expected_item
        mock_get_idp.assert_called_once_with(session=session, idp_id=config.idp_id)
        mock_add_item.assert_called_once_with(
            session=session,
            entity=IdpOverrides,
            idp=idp,
            provider=provider,
            created_by=created_by,
            updated_by=created_by,
            **config.overrides.model_dump(),
        )


def test_update_idp_calls_update_item(session):
    """Test update_idp_overrides calls update_item with correct arguments."""
    idp_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    new_overrides = MagicMock()
    updated_by = MagicMock()
    with patch(
        "fed_mgr.v1.providers.identity_providers.crud.update_item"
    ) as mock_update_item:
        update_idp_overrides(
            session=session,
            idp_id=idp_id,
            provider_id=provider_id,
            new_overrides=new_overrides,
            updated_by=updated_by,
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=IdpOverrides,
            idp_id=idp_id,
            provider_id=provider_id,
            updated_by=updated_by,
            **new_overrides.model_dump(),
        )


def test_delete_idp_calls_delete_item(session):
    """Test disconnect_prov_idp calls delete_item with correct arguments."""
    idp_id = uuid.uuid4()
    provider_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.identity_providers.crud.delete_item"
    ) as mock_delete_item:
        disconnect_prov_idp(session=session, idp_id=idp_id, provider_id=provider_id)
        mock_delete_item.assert_called_once_with(
            session=session,
            entity=IdpOverrides,
            idp_id=idp_id,
            provider_id=provider_id,
        )
