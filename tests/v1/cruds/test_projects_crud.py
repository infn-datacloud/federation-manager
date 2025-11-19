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

import pytest

from fed_mgr.exceptions import DeleteFailedError
from fed_mgr.v1.identity_providers.user_groups.slas.projects.crud import (
    connect_proj_to_sla,
    disconnect_proj_from_sla,
)
from fed_mgr.v1.models import SLA, Project, Provider, User
from fed_mgr.v1.providers.projects.crud import (
    add_project,
    delete_project,
    get_project,
    get_projects,
    update_project,
)
from fed_mgr.v1.providers.projects.schemas import ProjectCreate
from fed_mgr.v1.providers.schemas import ProviderStatus


def test_get_project_found(session):
    """Test get_project returns the Project if found."""
    project_id = uuid.uuid4()
    expected_project = MagicMock(spec=Project)
    with patch(
        "fed_mgr.v1.providers.projects.crud.get_item",
        return_value=expected_project,
    ) as mock_get_item:
        result = get_project(session=session, project_id=project_id)
        mock_get_item.assert_called_once_with(
            session=session, entity=Project, id=project_id
        )
        assert result == expected_project


def test_get_project_not_found(session):
    """Test get_project returns None if Project not found."""
    project_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.projects.crud.get_item",
        return_value=None,
    ) as mock_get_item:
        result = get_project(session=session, project_id=project_id)
        mock_get_item.assert_called_once_with(
            session=session, entity=Project, id=project_id
        )
        assert result is None


def test_get_projects(session):
    """Test get_projects calls get_items with correct arguments."""
    expected_list = [MagicMock(spec=Project), MagicMock(spec=Project)]
    expected_count = 2
    with patch(
        "fed_mgr.v1.providers.projects.crud.get_items",
        return_value=(expected_list, expected_count),
    ) as mock_get_items:
        result = get_projects(session=session, skip=0, limit=10, sort="name")
        mock_get_items.assert_called_once_with(
            session=session, entity=Project, skip=0, limit=10, sort="name"
        )
        assert result == (expected_list, expected_count)


def test_add_project_success(session):
    """Test add_project calls add_item with correct arguments and location exists."""
    project = MagicMock(spec=ProjectCreate)
    created_by = MagicMock(spec=User)
    provider = MagicMock(spec=Provider)
    expected_item = MagicMock(spec=Project)
    with patch(
        "fed_mgr.v1.providers.projects.crud.add_item", return_value=expected_item
    ) as mock_add_item:
        result = add_project(
            session=session, project=project, created_by=created_by, provider=provider
        )
        mock_add_item.assert_called_once_with(
            session=session,
            entity=Project,
            created_by=created_by,
            updated_by=created_by,
            provider=provider,
            **project.model_dump(),
        )
        assert result == expected_item


def test_update_project(session):
    """Test update_project calls update_item with correct arguments and location."""
    project_id = uuid.uuid4()
    new_project = MagicMock(spec=ProjectCreate)
    updated_by = MagicMock(spec=User)
    with patch(
        "fed_mgr.v1.providers.projects.crud.update_item", return_value=None
    ) as mock_update_item:
        result = update_project(
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
        )
        assert result is None


def test_delete_project(session):
    """Test delete_project calls delete_item with correct arguments."""
    project_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.projects.crud.delete_item", return_value=None
    ) as mock_delete_item:
        result = delete_project(session=session, project_id=project_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=Project, id=project_id
        )
        assert result is None


def test_connect_proj_to_sla(session):
    """Connect a non-root project to an SLA."""
    project = MagicMock(spec=Project)
    project.is_root = False
    project.provider = MagicMock(spec=Provider)
    project.provider.status = ProviderStatus.submitted
    sla = MagicMock(spec=Project)
    updated_by = MagicMock(spec=User)
    connect_proj_to_sla(
        session=session, updated_by=updated_by, project=project, sla=sla
    )
    session.add.assert_called_once_with(project)
    session.commit.assert_called_once()
    assert project.provider.status == ProviderStatus.submitted
    assert project.sla == sla
    assert project.updated_by == updated_by


def test_connect_root_proj_to_sla(session):
    """Connect a root project to an SLA.

    When the provider status is `draft `, this change to `ready`, otherwise it does not
    change.
    """
    project = MagicMock(spec=Project)
    project.is_root = True
    project.provider = MagicMock(spec=Provider)
    project.provider.status = ProviderStatus.submitted
    sla = MagicMock(spec=Project)
    updated_by = MagicMock(spec=User)

    # Connect and update provider state
    connect_proj_to_sla(
        session=session, updated_by=updated_by, project=project, sla=sla
    )
    session.add.assert_called_once_with(project)
    session.commit.assert_called_once()
    assert project.provider.status == ProviderStatus.ready
    assert project.sla == sla
    assert project.updated_by == updated_by

    session.reset_mock()
    # Connect and do not update provider state
    connect_proj_to_sla(
        session=session, updated_by=updated_by, project=project, sla=sla
    )
    session.add.assert_called_once_with(project)
    session.commit.assert_called_once()
    assert project.provider.status == ProviderStatus.ready
    assert project.sla == sla
    assert project.updated_by == updated_by


def test_disconnect_proj_from_sla(session):
    """Disconnect a project from its SLA.

    It does not matter if the project has or does not have an SLA.
    """
    project = MagicMock(spec=Project)
    project.is_root = False
    project.provider = MagicMock(spec=Provider)
    project.provider.status = ProviderStatus.submitted
    updated_by = MagicMock(spec=User)
    disconnect_proj_from_sla(session=session, updated_by=updated_by, project=project)
    session.add.assert_called_once_with(project)
    session.commit.assert_called_once()
    assert project.provider.status == ProviderStatus.submitted
    assert project.sla is None
    assert project.updated_by == updated_by


def test_disconnect_root_proj_from_sla(session):
    """Disconnect a root project from its SLA when the provider is `ready`."""
    project = MagicMock(spec=Project)
    project.is_root = True
    project.provider = MagicMock(spec=Provider)
    project.provider.status = ProviderStatus.ready
    project.sla = MagicMock(spec=SLA)
    updated_by = MagicMock(spec=User)
    disconnect_proj_from_sla(session=session, updated_by=updated_by, project=project)
    session.add.assert_called_once_with(project)
    session.commit.assert_called_once()
    assert project.provider.status == ProviderStatus.submitted
    assert project.sla is None
    assert project.updated_by == updated_by


def test_fail_disconnect_root_proj_from_sla(session):
    """Fail to disconnect a root project from a SLA.

    This happens when the provider is not `ready`.
    """
    project = MagicMock(spec=Project)
    project.is_root = True
    project.provider = MagicMock(spec=Provider)
    project.provider.status = ProviderStatus.draft
    project.sla = MagicMock(spec=SLA)
    updated_by = MagicMock(spec=User)
    with pytest.raises(
        DeleteFailedError,
        match="The SLA of the root project can't be removed if the hosting provider is "
        f"not in the {ProviderStatus.ready.name} state",
    ):
        disconnect_proj_from_sla(
            session=session, updated_by=updated_by, project=project
        )
    session.add.assert_not_called()
    session.commit.assert_not_called()
