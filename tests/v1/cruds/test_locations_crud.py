"""Unit tests for fed_mgr.v1.locations.crud.

Tests in this file:
- test_get_location_found
- test_get_location_not_found
- test_get_locations
- test_add_location
- test_update_location
- test_delete_location
"""

import uuid
from unittest.mock import MagicMock, patch

from fed_mgr.v1.locations.crud import (
    add_location,
    delete_location,
    get_location,
    get_locations,
    update_location,
)
from fed_mgr.v1.models import Location


def test_get_location_found(session):
    """Test get_location returns the Location if found."""
    location_id = uuid.uuid4()
    expected_location = MagicMock()
    with patch(
        "fed_mgr.v1.locations.crud.get_item",
        return_value=expected_location,
    ) as mock_get_item:
        result = get_location(session=session, location_id=location_id)
        assert result == expected_location
        mock_get_item.assert_called_once_with(
            session=session, entity=Location, id=location_id
        )


def test_get_location_not_found(session):
    """Test get_location returns None if Location not found."""
    location_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.locations.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_location(session=session, location_id=location_id)
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session, entity=Location, id=location_id
        )


def test_get_locations(session):
    """Test get_locations calls get_items with correct arguments."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.locations.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_locations(session=session, skip=0, limit=10, sort="name")
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session, entity=Location, skip=0, limit=10, sort="name"
        )


def test_add_location(session):
    """Test add_location calls add_item with correct arguments."""
    location = MagicMock()
    created_by = MagicMock()
    expected_item = MagicMock()
    with patch(
        "fed_mgr.v1.locations.crud.add_item",
        return_value=expected_item,
    ) as mock_add_item:
        result = add_location(session=session, location=location, created_by=created_by)
        assert result == expected_item
        mock_add_item.assert_called_once_with(
            session=session,
            entity=Location,
            created_by=created_by,
            updated_by=created_by,
            **location.model_dump(),
        )


def test_update_location(session):
    """Test update_location calls update_item with correct arguments."""
    location_id = uuid.uuid4()
    new_location = MagicMock()
    updated_by = MagicMock()
    with patch("fed_mgr.v1.locations.crud.update_item") as mock_update_item:
        update_location(
            session=session,
            location_id=location_id,
            new_location=new_location,
            updated_by=updated_by,
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=Location,
            id=location_id,
            updated_by=updated_by,
            **new_location.model_dump(),
        )


def test_delete_location(session):
    """Test delete_location calls delete_item with correct arguments."""
    location_id = uuid.uuid4()
    with patch("fed_mgr.v1.locations.crud.delete_item") as mock_delete_item:
        delete_location(session=session, location_id=location_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=Location, id=location_id
        )
