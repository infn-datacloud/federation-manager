"""Unit tests for fed_mgr.v1.providers.regions.crud.

Tests in this file:
- test_get_region_found
- test_get_region_not_found
- test_get_regions
- test_add_region_success
- test_add_region_location_not_found
- test_update_region_success
- test_update_region_location_not_found
- test_delete_region
- test_check_location_exist_found
- test_check_location_exist_not_found
"""

import uuid
from unittest.mock import MagicMock, patch

from fed_mgr.v1.models import Provider, Region, User
from fed_mgr.v1.providers.regions.crud import (
    add_region,
    delete_region,
    get_region,
    get_regions,
    update_region,
)
from fed_mgr.v1.providers.regions.schemas import RegionCreate


def test_get_region_found(session):
    """Test get_region returns the Region if found."""
    region_id = uuid.uuid4()
    expected_region = MagicMock(spec=Region)
    with patch(
        "fed_mgr.v1.providers.regions.crud.get_item",
        return_value=expected_region,
    ) as mock_get_item:
        result = get_region(session=session, region_id=region_id)
        mock_get_item.assert_called_once_with(
            session=session, entity=Region, id=region_id
        )
        assert result == expected_region


def test_get_region_not_found(session):
    """Test get_region returns None if Region not found."""
    region_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.regions.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_region(session=session, region_id=region_id)
        mock_get_item.assert_called_once_with(
            session=session, entity=Region, id=region_id
        )
        assert result is None


def test_get_regions(session):
    """Test get_regions calls get_items with correct arguments."""
    expected_list = [MagicMock(spec=Region), MagicMock(spec=Region)]
    expected_count = 2
    with patch(
        "fed_mgr.v1.providers.regions.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_regions(session=session, skip=0, limit=10, sort="name")
        mock_get_items.assert_called_once_with(
            session=session, entity=Region, skip=0, limit=10, sort="name"
        )
        assert result == (expected_list, expected_count)


def test_add_region_success(session):
    """Test add_region calls add_item with correct arguments and location exists."""
    region = MagicMock(spec=RegionCreate)
    created_by = MagicMock(spec=User)
    expected_item = MagicMock(spec=Region)
    provider = MagicMock(spec=Provider)
    with patch(
        "fed_mgr.v1.providers.regions.crud.add_item",
        return_value=expected_item,
    ) as mock_add_item:
        result = add_region(
            session=session, region=region, created_by=created_by, provider=provider
        )
        mock_add_item.assert_called_once_with(
            session=session,
            entity=Region,
            created_by=created_by,
            updated_by=created_by,
            provider=provider,
            **region.model_dump(),
        )
        assert result == expected_item


def test_update_region_success(session):
    """Test update_region calls update_item with correct arguments and location."""
    region_id = uuid.uuid4()
    new_region = MagicMock(spec=RegionCreate)
    updated_by = MagicMock(spec=User)
    with patch(
        "fed_mgr.v1.providers.regions.crud.update_item", return_value=None
    ) as mock_update_item:
        result = update_region(
            session=session,
            region_id=region_id,
            new_region=new_region,
            updated_by=updated_by,
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=Region,
            id=region_id,
            updated_by=updated_by,
        )
        assert result is None


def test_delete_region(session):
    """Test delete_region calls delete_item with correct arguments."""
    region_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.regions.crud.delete_item", return_value=None
    ) as mock_delete_item:
        result = delete_region(session=session, region_id=region_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=Region, id=region_id
        )
        assert result is None
