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

import pytest

from fed_mgr.exceptions import LocationNotFoundError
from fed_mgr.v1.models import Region
from fed_mgr.v1.providers.regions.crud import (
    add_region,
    check_location_exist,
    delete_region,
    get_region,
    get_regions,
    update_region,
)
from fed_mgr.v1.providers.regions.schemas import RegionCreate


def test_get_region_found(session):
    """Test get_region returns the Region if found."""
    region_id = uuid.uuid4()
    expected_region = MagicMock()
    with patch(
        "fed_mgr.v1.providers.regions.crud.get_item",
        return_value=expected_region,
    ) as mock_get_item:
        result = get_region(session=session, region_id=region_id)
        assert result == expected_region
        mock_get_item.assert_called_once_with(
            session=session, entity=Region, item_id=region_id
        )


def test_get_region_not_found(session):
    """Test get_region returns None if Region not found."""
    region_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.regions.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_region(session=session, region_id=region_id)
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session, entity=Region, item_id=region_id
        )


def test_get_regions(session):
    """Test get_regions calls get_items with correct arguments."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.providers.regions.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_regions(session=session, skip=0, limit=10, sort="name")
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session, entity=Region, skip=0, limit=10, sort="name"
        )


def test_add_region_success(session):
    """Test add_region calls add_item with correct arguments and location exists."""
    region = MagicMock(spec=RegionCreate)
    created_by = MagicMock()
    created_by.id = uuid.uuid4()
    location = MagicMock()
    provider = MagicMock()
    region.model_dump.return_value = {"foo": "bar"}
    with (
        patch(
            "fed_mgr.v1.providers.regions.crud.check_location_exist",
            return_value=location,
        ) as mock_check_loc,
        patch(
            "fed_mgr.v1.providers.regions.crud.add_item",
            return_value=location,
        ) as mock_add_item,
    ):
        result = add_region(
            session=session, region=region, created_by=created_by, provider=provider
        )
        assert result == location
        mock_check_loc.assert_called_once_with(session=session, region=region)
        mock_add_item.assert_called_once_with(
            session=session,
            entity=Region,
            created_by=created_by.id,
            updated_by=created_by.id,
            location=location,
            provider=provider,
            **region.model_dump(),
        )


def test_add_region_location_not_found(session):
    """Test add_region raises LocationNotFoundError if location does not exist."""
    region = MagicMock(spec=RegionCreate)
    created_by = MagicMock()
    provider = MagicMock()
    with patch(
        "fed_mgr.v1.providers.regions.crud.check_location_exist",
        side_effect=LocationNotFoundError("not found"),
    ):
        with pytest.raises(LocationNotFoundError) as exc:
            add_region(
                session=session, region=region, created_by=created_by, provider=provider
            )
        assert "not found" in str(exc.value)


def test_update_region_success(session):
    """Test update_region calls update_item with correct arguments and location."""
    region_id = uuid.uuid4()
    new_region = MagicMock(spec=RegionCreate)
    updated_by = MagicMock()
    updated_by.id = uuid.uuid4()
    location = MagicMock()
    new_region.location_id = uuid.uuid4()
    new_region.model_dump.return_value = {"foo": "bar"}
    with (
        patch(
            "fed_mgr.v1.providers.regions.crud.check_location_exist",
            return_value=location,
        ) as mock_check_loc,
        patch("fed_mgr.v1.providers.regions.crud.update_item") as mock_update_item,
    ):
        update_region(
            session=session,
            region_id=region_id,
            new_region=new_region,
            updated_by=updated_by,
        )
        mock_check_loc.assert_called_once_with(session=session, region=new_region)
        mock_update_item.assert_called_once_with(
            session=session,
            entity=Region,
            item_id=region_id,
            updated_by=updated_by.id,
            foo="bar",
            location=location,
        )


def test_update_region_location_not_found(session):
    """Test update_region raises LocationNotFoundError if location does not exist."""
    region_id = uuid.uuid4()
    new_region = MagicMock(spec=RegionCreate)
    updated_by = MagicMock()
    new_region.location_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.regions.crud.check_location_exist",
        side_effect=LocationNotFoundError("not found"),
    ):
        with pytest.raises(LocationNotFoundError) as exc:
            update_region(
                session=session,
                region_id=region_id,
                new_region=new_region,
                updated_by=updated_by,
            )
        assert "not found" in str(exc.value)


def test_delete_region(session):
    """Test delete_region calls delete_item with correct arguments."""
    region_id = uuid.uuid4()
    with patch("fed_mgr.v1.providers.regions.crud.delete_item") as mock_delete_item:
        delete_region(session=session, region_id=region_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=Region, item_id=region_id
        )


def test_check_location_exist_found(session):
    """Test check_location_exist returns location if found."""
    region = MagicMock()
    location = MagicMock()
    region.location_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.regions.crud.get_location",
        return_value=location,
    ) as mock_get_location:
        result = check_location_exist(session=session, region=region)
        assert result == location
        mock_get_location.assert_called_once_with(
            session=session, location_id=region.location_id
        )


def test_check_location_exist_not_found(session):
    """Test check_location_exist raises LocationNotFoundError if not found."""
    region = MagicMock()
    region.location_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.regions.crud.get_location",
        return_value=None,
    ):
        with pytest.raises(LocationNotFoundError) as exc:
            check_location_exist(session=session, region=region)
        assert str(region.location_id) in str(exc.value)
