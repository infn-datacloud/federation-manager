"""Unit tests for fed_mgr.v1.providers.projects.regions.crud.

Tests in this file:
- test_get_proj_reg_config_calls_get_item
- test_get_proj_reg_configs_calls_get_items
- test_add_proj_reg_config_calls_add_item
- test_update_proj_reg_config_calls_update_item
- test_delete_proj_reg_config_calls_delete_item
"""

import uuid
from unittest.mock import MagicMock, patch

from fed_mgr.v1.models import RegionOverrides
from fed_mgr.v1.providers.projects.regions.crud import (
    connect_project_region,
    disconnect_project_region,
    get_region_overrides,
    get_region_overrides_list,
    update_region_overrides,
)


def test_get_proj_reg_config_found(session):
    """Test get_region_overrides returns the Provider-IdP relationship if found."""
    region_id = uuid.uuid4()
    project_id = uuid.uuid4()
    expected_region = MagicMock()
    with patch(
        "fed_mgr.v1.providers.projects.regions.crud.get_item",
        return_value=expected_region,
    ) as mock_get_item:
        result = get_region_overrides(
            session=session, region_id=region_id, project_id=project_id
        )
        assert result == expected_region
        mock_get_item.assert_called_once_with(
            session=session,
            entity=RegionOverrides,
            region_id=region_id,
            project_id=project_id,
        )


def test_get_region_not_found(session):
    """Test get_region_overrides returns None if Provider-IdP relationship not found."""
    region_id = uuid.uuid4()
    project_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.projects.regions.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_region_overrides(
            session=session, region_id=region_id, project_id=project_id
        )
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session,
            entity=RegionOverrides,
            region_id=region_id,
            project_id=project_id,
        )


def test_get_regions(session):
    """Test get_region_overrides_list calls get_items with correct arguments."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.providers.projects.regions.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_region_overrides_list(
            session=session, skip=0, limit=10, sort="name"
        )
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session, entity=RegionOverrides, skip=0, limit=10, sort="name"
        )


def test_add_region_calls_add_item(session):
    """Test connect_project_region calls add_item with correct arguments."""
    config = MagicMock()
    region = MagicMock()
    project = MagicMock()
    created_by = MagicMock()
    expected_item = MagicMock()
    with (
        patch(
            "fed_mgr.v1.providers.projects.regions.crud.add_item",
            return_value=expected_item,
        ) as mock_add_item,
        patch(
            "fed_mgr.v1.providers.projects.regions.crud.get_region",
            return_value=region,
        ) as mock_get_region,
    ):
        result = connect_project_region(
            session=session,
            config=config,
            project=project,
            created_by=created_by,
        )
        assert result == expected_item
        mock_get_region.assert_called_once_with(
            session=session, region_id=config.region_id
        )
        mock_add_item.assert_called_once_with(
            session=session,
            entity=RegionOverrides,
            region=region,
            project=project,
            created_by=created_by,
            updated_by=created_by,
            **config.overrides.model_dump(),
        )


def test_update_region_calls_update_item(session):
    """Test update_region_overrides calls update_item with correct arguments."""
    region_id = uuid.uuid4()
    project_id = uuid.uuid4()
    new_overrides = MagicMock()
    updated_by = MagicMock()
    with patch(
        "fed_mgr.v1.providers.projects.regions.crud.update_item"
    ) as mock_update_item:
        update_region_overrides(
            session=session,
            region_id=region_id,
            project_id=project_id,
            new_overrides=new_overrides,
            updated_by=updated_by,
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=RegionOverrides,
            region_id=region_id,
            project_id=project_id,
            updated_by=updated_by,
            **new_overrides.model_dump(),
        )


def test_delete_region_calls_delete_item(session):
    """Test disconnect_project_region calls delete_item with correct arguments."""
    region_id = uuid.uuid4()
    project_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.projects.regions.crud.delete_item"
    ) as mock_delete_item:
        disconnect_project_region(
            session=session, region_id=region_id, project_id=project_id
        )
        mock_delete_item.assert_called_once_with(
            session=session,
            entity=RegionOverrides,
            region_id=region_id,
            project_id=project_id,
        )
