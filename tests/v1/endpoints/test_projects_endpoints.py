"""Integration tests for fed_mgr.v1.providers.projects.endpoints.

Tests in this file:
- test_options_projects
- test_create_project_success
- test_create_project_conflict
- test_create_project_not_null_error
- test_create_project_location_not_found
- test_get_projects_success
- test_get_project_success
- test_get_project_not_found
- test_edit_project_success
- test_edit_project_not_found
- test_edit_project_conflict
- test_edit_project_not_null_error
- test_edit_project_location_not_found
- test_delete_project_success
"""

import uuid
from unittest.mock import patch

from fed_mgr.exceptions import ConflictError, DeleteFailedError, ItemNotFoundError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.models import Project
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.projects.crud import get_project
from fed_mgr.v1.providers.projects.schemas import ProjectCreate
from fed_mgr.v1.schemas import ItemID


# OPTIONS endpoint
def test_options_projects_parent_provider_not_found(client):
    """Test OPTIONS returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.options(f"/api/v1/providers/{fake_provider_id}/projects/")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_options_projects(client, provider_dep):
    """Test OPTIONS /providers/{provider_id}/projects/ returns 204 and Allow header."""
    resp = client.options(f"/api/v1/providers/{provider_dep.id}/projects/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


# POST endpoint
def test_create_project_parent_provider_not_found(client, project_data):
    """Test POST returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/", json=project_data
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_create_project_success(
    client, session, current_user, provider_dep, project_data
):
    """Test POST /projects/ creates a project and returns 201 with id."""
    fake_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.projects.endpoints.add_project",
        return_value=ItemID(id=fake_id),
    ) as mock_create:
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/projects/", json=project_data
        )
        mock_create.assert_called_once_with(
            session=session,
            project=ProjectCreate(**project_data),
            created_by=current_user,
            provider=provider_dep,
        )
        assert resp.status_code == 201
        assert resp.json() == {"id": str(fake_id)}


def test_create_project_conflict(
    client, session, current_user, provider_dep, project_data
):
    """Test POST /projects/ returns 409 if project already exists."""
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.providers.projects.endpoints.add_project",
        side_effect=ConflictError(err_msg),
    ) as mock_create:
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/projects/", json=project_data
        )
        mock_create.assert_called_once_with(
            session=session,
            project=ProjectCreate(**project_data),
            created_by=current_user,
            provider=provider_dep,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


# GET (list) endpoint
def test_get_projects_parent_provider_not_found(client):
    """Test GET returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/projects/")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_get_projects_success(client, session, provider_dep, project_data):
    """Test GET /projects/ returns paginated project list."""
    with patch(
        "fed_mgr.v1.providers.projects.endpoints.get_projects",
        return_value=([], 0),
    ) as mock_get:
        resp = client.get(f"/api/v1/providers/{provider_dep.id}/projects/")
        mock_get.assert_called_once_with(
            session=session,
            skip=0,
            limit=5,
            sort="-created_at",
            provider_id=provider_dep.id,
            sla_id=None,
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 0
        assert "page" in resp.json()
        assert "links" in resp.json()

    fake_id = uuid.uuid4()
    user_id = uuid.uuid4()
    project1 = Project(
        **project_data,
        id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
        provider_id=provider_dep.id,
    )
    with patch(
        "fed_mgr.v1.providers.projects.endpoints.get_projects",
        return_value=([project1], 1),
    ) as mock_get:
        resp = client.get(f"/api/v1/providers/{provider_dep.id}/projects/")
        mock_get.assert_called_once_with(
            session=session,
            skip=0,
            limit=5,
            sort="-created_at",
            provider_id=provider_dep.id,
            sla_id=None,
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 1
        assert "page" in resp.json()
        assert "links" in resp.json()

    project2 = Project(
        **project_data,
        id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
        provider_id=provider_dep.id,
    )
    with patch(
        "fed_mgr.v1.providers.projects.endpoints.get_projects",
        return_value=([project1, project2], 2),
    ) as mock_get:
        resp = client.get(f"/api/v1/providers/{provider_dep.id}/projects/")
        mock_get.assert_called_once_with(
            session=session,
            skip=0,
            limit=5,
            sort="-created_at",
            provider_id=provider_dep.id,
            sla_id=None,
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 2
        assert "page" in resp.json()
        assert "links" in resp.json()


# GET (by id) endpoint
def test_get_project_parent_provider_not_found(client):
    """Test GET by id returns 404 if parent_provider is None."""
    fake_id = uuid.uuid4()
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None
    sub_app_v1.dependency_overrides[get_project] = lambda: None

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_get_project_success(client, provider_dep, project_dep):
    """Test GET by id returns user group."""
    resp = client.get(f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(project_dep.id)


def test_get_project_not_found(client, provider_dep):
    """Test GET by id returns 404 if not found."""
    fake_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_project] = lambda: None

    resp = client.get(f"/api/v1/providers/{provider_dep.id}/projects/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert f"Project with ID '{fake_id}' does not exist" == resp.json()["detail"]


# PUT endpoint
def test_edit_project_parent_provider_not_found(client, project_data):
    """Test PUT returns 404 if parent_provider is None."""
    fake_id = uuid.uuid4()
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}", json=project_data
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_edit_project_success(
    client, session, current_user, provider_dep, project_data
):
    """Test PUT returns 204 on success."""
    fake_id = uuid.uuid4()

    with patch(
        "fed_mgr.v1.providers.projects.endpoints.update_project",
        return_value=None,
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/projects/{fake_id}", json=project_data
        )
        mock_edit.assert_called_once_with(
            session=session,
            project_id=fake_id,
            new_project=ProjectCreate(**project_data),
            updated_by=current_user,
        )
        assert resp.status_code == 204


def test_edit_project_not_found(
    client, session, current_user, provider_dep, project_data
):
    """Test PUT returns 404 if not found."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.providers.projects.endpoints.update_project",
        side_effect=ItemNotFoundError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/projects/{fake_id}", json=project_data
        )
        mock_edit.assert_called_once_with(
            session=session,
            project_id=fake_id,
            new_project=ProjectCreate(**project_data),
            updated_by=current_user,
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert resp.json()["detail"] == err_msg


def test_edit_project_conflict(
    client, session, current_user, provider_dep, project_data
):
    """Test PUT returns 409 if conflict."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.providers.projects.endpoints.update_project",
        side_effect=ConflictError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/projects/{fake_id}", json=project_data
        )
        mock_edit.assert_called_once_with(
            session=session,
            project_id=fake_id,
            new_project=ProjectCreate(**project_data),
            updated_by=current_user,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


# DELETE endpoint
def test_delete_project_parent_provider_not_found(client):
    """Test DELETE returns 404 if parent_provider is None."""
    fake_id = uuid.uuid4()
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_delete_project_success(client, session, provider_dep):
    """Test DELETE returns 204 on success."""
    fake_id = uuid.uuid4()

    with patch(
        "fed_mgr.v1.providers.projects.endpoints.delete_project",
        return_value=None,
    ) as mock_delete:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/projects/{fake_id}")
        mock_delete.assert_called_once_with(session=session, project_id=fake_id)
        assert resp.status_code == 204


def test_delete_project_fail(client, session, provider_dep):
    """Test DELETE /projects/{project_id} returns 400 on fail."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.providers.projects.endpoints.delete_project",
        side_effect=DeleteFailedError(err_msg),
    ) as mock_delete:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/projects/{fake_id}")
        mock_delete.assert_called_once_with(session=session, project_id=fake_id)
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg
