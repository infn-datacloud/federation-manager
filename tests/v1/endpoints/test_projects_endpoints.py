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

from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    NoItemToUpdateError,
    NotNullError,
)
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.projects.crud import get_project

DUMMY_NAME = "eu-west-1"
DUMMY_DESC = "A test project."
DUMMY_IAAS_ID = "12345"
DUMMY_CREATED_AT = "2024-01-01T00:00:00Z"


def get_fake_provider_id() -> str:
    """Patch get_idp depencency to return a dummy IDP."""
    fake_id = str(uuid.uuid4())

    class FakeProvider:
        id = fake_id

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: FakeProvider()
    )

    return fake_id


def fake_add_project(fake_id):
    """Return a fake project object with the given id."""

    class FakeProject:
        id = fake_id

    return FakeProject()


def test_options_projects_parent_provider_not_found(client):
    """Test OPTIONS returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.options(f"/api/v1/providers/{fake_provider_id}/projects/")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_options_projects(client):
    """Test OPTIONS /providers/{provider_id}/projects/ returns 204 and Allow header."""
    fake_provider_id = get_fake_provider_id()

    resp = client.options(f"/api/v1/providers/{fake_provider_id}/projects/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_project_parent_provider_not_found(client):
    """Test POST returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())
    project_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "iaas_project_id": DUMMY_IAAS_ID,
    }

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/", json=project_data
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_create_project_success(client, monkeypatch):
    """Test POST /projects/ creates a project and returns 201 with id."""
    fake_id = str(uuid.uuid4())
    fake_provider_id = get_fake_provider_id()
    project_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "iaas_project_id": DUMMY_IAAS_ID,
    }
    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.add_project",
        lambda session, project, created_by, provider: fake_add_project(fake_id),
    )
    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/", json=project_data
    )
    assert resp.status_code == 201
    assert resp.json() == {"id": fake_id}


def test_create_project_conflict(client, monkeypatch):
    """Test POST /projects/ returns 409 if project already exists."""
    fake_provider_id = get_fake_provider_id()
    project_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "iaas_project_id": DUMMY_IAAS_ID,
    }

    def fake_add_project(session, project, created_by, provider):
        raise ConflictError("Project already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.add_project", fake_add_project
    )
    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/", json=project_data
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Project already exists"


def test_create_project_not_null_error(client, monkeypatch):
    """Test POST /projects/ returns 422 if a not null error occurs."""
    fake_provider_id = get_fake_provider_id()
    project_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "iaas_project_id": DUMMY_IAAS_ID,
    }

    def fake_add_project(session, project, created_by, provider):
        raise NotNullError("Field 'name' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.add_project", fake_add_project
    )
    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/", json=project_data
    )
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


def test_get_projects_parent_provider_not_found(client):
    """Test GET returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/projects/")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_projects_success(client, monkeypatch):
    """Test GET /projects/ returns paginated project list."""
    fake_provider_id = get_fake_provider_id()
    fake_projects = []
    fake_total = 0

    def fake_get_projects(session, skip, limit, sort, **kwargs):
        return fake_projects, fake_total

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.get_projects", fake_get_projects
    )
    resp = client.get(f"/api/v1/providers/{fake_provider_id}/projects/")
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_get_project_parent_provider_not_found(client):
    """Test GET by id returns 404 if parent_provider is None."""
    fake_id = str(uuid.uuid4())
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )
    sub_app_v1.dependency_overrides[get_project] = lambda project_id, session=None: None

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_project_success(client):
    """Test GET /projects/{project_id} returns project if found."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())

    class FakeProject:
        id = fake_id
        name = DUMMY_NAME
        description = DUMMY_DESC
        iaas_project_id = DUMMY_IAAS_ID
        created_at = DUMMY_CREATED_AT
        created_by_id = fake_id
        updated_at = DUMMY_CREATED_AT
        updated_by_id = fake_id

        def model_dump(self):
            return {
                "id": self.id,
                "name": self.name,
                "description": self.description,
                "iaas_project_id": self.iaas_project_id,
                "created_at": self.created_at,
                "created_by_id": self.created_by_id,
                "updated_at": self.updated_at,
                "updated_by_id": self.updated_by_id,
            }

    def fake_get_project(project_id, session=None):
        return FakeProject()

    sub_app_v1.dependency_overrides[get_project] = fake_get_project
    resp = client.get(f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == fake_id


def test_get_project_not_found(client):
    """Test GET /projects/{project_id} returns 404 if not found."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    sub_app_v1.dependency_overrides[get_project] = lambda project_id, session=None: None
    resp = client.get(f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_project_parent_prpvider_not_found(client):
    """Test PUT returns 404 if parent_provider is None."""
    fake_id = str(uuid.uuid4())
    fake_provider_id = str(uuid.uuid4())
    project_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "iaas_project_id": DUMMY_IAAS_ID,
    }

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}", json=project_data
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_project_success(client, monkeypatch):
    """Test PUT /projects/{project_id} returns 204 on successful update."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    project_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "iaas_project_id": DUMMY_IAAS_ID,
    }

    def fake_update_project(session, project_id, new_project, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.update_project", fake_update_project
    )
    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}", json=project_data
    )
    assert resp.status_code == 204


def test_edit_project_not_found(client, monkeypatch):
    """Test PUT /projects/{project_id} returns 404 if not found."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    project_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "iaas_project_id": DUMMY_IAAS_ID,
    }

    def fake_update_project(session, project_id, new_project, updated_by):
        raise NoItemToUpdateError("Project not found")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.update_project", fake_update_project
    )
    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}", json=project_data
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Project not found"


def test_edit_project_conflict(client, monkeypatch):
    """Test PUT /projects/{project_id} returns 409 if conflict error occurs."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    project_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "iaas_project_id": DUMMY_IAAS_ID,
    }

    def fake_update_project(session, project_id, new_project, updated_by):
        raise ConflictError("Project already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.update_project", fake_update_project
    )
    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}", json=project_data
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Project already exists"


def test_edit_project_not_null_error(client, monkeypatch):
    """Test PUT /projects/{project_id} returns 422 if not null error occurs."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    project_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "iaas_project_id": DUMMY_IAAS_ID,
    }

    def fake_update_project(session, project_id, new_project, updated_by):
        raise NotNullError("Field 'name' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.update_project", fake_update_project
    )
    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}", json=project_data
    )
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


def test_delete_project_parent_provider_not_found(client):
    """Test DELETE returns 404 if parent_provider is None."""
    fake_id = str(uuid.uuid4())
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_delete_project_success(client, monkeypatch):
    """Test DELETE /projects/{project_id} returns 204 on success."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.delete_project",
        lambda session, project_id: None,
    )
    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}")
    assert resp.status_code == 204


def test_delete_project_fail(client, monkeypatch):
    """Test DELETE /projects/{project_id} returns 400 on fail."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())

    def fake_delete_project(session, project_id):
        raise DeleteFailedError("Failed to delete item")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.endpoints.delete_project", fake_delete_project
    )

    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/projects/{fake_id}")
    assert resp.status_code == 400
