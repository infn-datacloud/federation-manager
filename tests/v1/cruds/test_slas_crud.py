"""Unit tests for SLA CRUD utility functions.

These tests cover the CRUD logic in fed_mgr.v1.identity_providers.user_groups.slas.crud.
"""

import uuid
from unittest.mock import MagicMock, patch

from fed_mgr.v1.identity_providers.user_groups.slas.crud import (
    add_sla,
    delete_sla,
    get_sla,
    get_slas,
    update_sla,
)
from fed_mgr.v1.identity_providers.user_groups.slas.schemas import SLA


def test_get_sla_found(session):
    """Test get_sla returns the SLA if found."""
    sla_id = uuid.uuid4()
    expected_sla = MagicMock()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.slas.crud.get_item",
        return_value=expected_sla,
    ) as mock_get_item:
        result = get_sla(session=session, sla_id=sla_id)
        assert result == expected_sla
        mock_get_item.assert_called_once_with(
            session=session, entity=SLA, item_id=sla_id
        )


def test_get_sla_not_found(session):
    """Test get_sla returns None if SLA not found."""
    sla_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.slas.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_sla(session=session, sla_id=sla_id)
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session, entity=SLA, item_id=sla_id
        )


def test_get_slas(session):
    """Test get_slas returns paginated and sorted list of SLAs and total count."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.slas.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_slas(
            session=session, skip=0, limit=10, sort="created_at", foo="bar"
        )
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session,
            entity=SLA,
            skip=0,
            limit=10,
            sort="created_at",
            foo="bar",
        )


def test_add_sla(session):
    """Test add_sla passes correct arguments and returns ItemID."""
    sla = MagicMock()
    created_by = MagicMock()
    created_by.id = uuid.uuid4()
    parent_user_group = MagicMock()
    parent_user_group.id = uuid.uuid4()
    expected_item = MagicMock()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.slas.crud.add_item",
        return_value=expected_item,
    ) as mock_add_item:
        result = add_sla(
            session=session,
            sla=sla,
            created_by=created_by,
            parent_user_group=parent_user_group,
        )
        assert result == expected_item
        mock_add_item.assert_called_once_with(
            session=session,
            entity=SLA,
            item=sla,
            created_by=created_by.id,
            updated_by=created_by.id,
            user_group=parent_user_group.id,
        )


def test_update_sla(session):
    """Test update_sla passes correct arguments to update_item."""
    sla_id = uuid.uuid4()
    new_sla = MagicMock()
    updated_by = MagicMock()
    updated_by.id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.slas.crud.update_item"
    ) as mock_update_item:
        update_sla(
            session=session,
            sla_id=sla_id,
            new_sla=new_sla,
            updated_by=updated_by,
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=SLA,
            item_id=sla_id,
            new_data=new_sla,
            updated_by=updated_by.id,
        )


def test_delete_sla(session):
    """Test delete_sla passes correct arguments to delete_item."""
    sla_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.slas.crud.delete_item"
    ) as mock_delete_item:
        delete_sla(session=session, sla_id=sla_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=SLA, item_id=sla_id
        )
