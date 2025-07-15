"""Unit tests for fed_mgr.v1.providers.projects.crud.

Tests in this file:
- test_get_project_found
- test_get_project_not_found
- test_get_projects
- test_add_project_success
- test_update_project_success
- test_delete_project
"""

import uuid
from unittest.mock import MagicMock, patch

from fed_mgr.v1.models import Project
from fed_mgr.v1.providers.projects.crud import (
    add_project,
    delete_project,
    get_project,
    get_projects,
    update_project,
)
from fed_mgr.v1.providers.projects.schemas import ProjectCreate


def test_get_project_found(session):
    """Test get_project returns the Project if found."""
    project_id = uuid.uuid4()
    expected_project = MagicMock()
    with patch(
        "fed_mgr.v1.providers.projects.crud.get_item",
        return_value=expected_project,
    ) as mock_get_item:
        result = get_project(session=session, project_id=project_id)
        assert result == expected_project
        mock_get_item.assert_called_once_with(
            session=session, entity=Project, id=project_id
        )


def test_get_project_not_found(session):
    """Test get_project returns None if Project not found."""
    project_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.projects.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_project(session=session, project_id=project_id)
        assert result is None
        mock_get_item.assert_called_once_with(
            session=session, entity=Project, id=project_id
        )


def test_get_projects(session):
    """Test get_projects calls get_items with correct arguments."""
    expected_list = [MagicMock(), MagicMock()]
    expected_count = 2
    with patch(
        "fed_mgr.v1.providers.projects.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_projects(session=session, skip=0, limit=10, sort="name")
        assert result == (expected_list, expected_count)
        mock_get_items.assert_called_once_with(
            session=session, entity=Project, skip=0, limit=10, sort="name"
        )


def test_add_project_success(session):
    """Test add_project calls add_item with correct arguments and location exists."""
    project = MagicMock(spec=ProjectCreate)
    created_by = MagicMock()
    provider = MagicMock()
    project.model_dump.return_value = {"foo": "bar"}
    expected_item = MagicMock()
    with patch(
        "fed_mgr.v1.providers.projects.crud.add_item", return_value=expected_item
    ) as mock_add_item:
        result = add_project(
            session=session, project=project, created_by=created_by, provider=provider
        )
        assert result == expected_item
        mock_add_item.assert_called_once_with(
            session=session,
            entity=Project,
            created_by=created_by,
            updated_by=created_by,
            provider=provider,
            **project.model_dump(),
        )


def test_update_project_success(session):
    """Test update_project calls update_item with correct arguments and location."""
    project_id = uuid.uuid4()
    new_project = MagicMock(spec=ProjectCreate)
    updated_by = MagicMock()
    new_project.model_dump.return_value = {"foo": "bar"}
    with (
        patch("fed_mgr.v1.providers.projects.crud.update_item") as mock_update_item,
    ):
        update_project(
            session=session,
            project_id=project_id,
            new_project=new_project,
            updated_by=updated_by,
        )
        mock_update_item.assert_called_once_with(
            session=session,
            entity=Project,
            id=project_id,
            updated_by=updated_by,
            foo="bar",
        )


def test_delete_project(session):
    """Test delete_project calls delete_item with correct arguments."""
    project_id = uuid.uuid4()
    with patch("fed_mgr.v1.providers.projects.crud.delete_item") as mock_delete_item:
        delete_project(session=session, project_id=project_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=Project, id=project_id
        )
