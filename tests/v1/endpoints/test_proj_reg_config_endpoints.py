"""Integration tests for fed_mgr.v1.providers.projects.regions.endpoints.

Tests in this file:
- test_options_regions
- test_create_region_success
- test_create_region_conflict
- test_create_region_not_null_error
- test_get_regions_success
- test_get_region_success
- test_get_region_not_found
- test_edit_region_success
- test_edit_region_not_found
- test_edit_region_conflict
- test_edit_region_not_null_error
- test_delete_region_success
"""

import uuid
from datetime import datetime

from sqlmodel import SQLModel

from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    ItemNotFoundError,
    NotNullError,
)
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.projects.crud import get_project
from fed_mgr.v1.providers.projects.regions.crud import get_region_overrides
from fed_mgr.v1.providers.regions.crud import get_region

DUMMY_ENDPOINT = "https://region.example.com"
DUMMY_NAME = "Test IdP"
DUMMY_CLAIM = "groups"
DUMMY_PROTOCOL = "openid"
DUMMY_AUD = "aud1"
DUMMY_CREATED_AT = datetime.now()


def get_fake_provider_id() -> str:
    """Patch get_povider depencency to return a dummy Provider."""
    fake_id = str(uuid.uuid4())

    class FakeProvider:
        id = fake_id

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda project_id, session=None: FakeProvider()
    )

    return fake_id


def get_fake_project_id() -> str:
    """Patch get_project depencency to return a dummy Project."""
    fake_id = str(uuid.uuid4())

    class FakeProject:
        id = fake_id

    sub_app_v1.dependency_overrides[get_project] = (
        lambda project_id, session=None: FakeProject()
    )

    return fake_id


def get_fake_region_id() -> str:
    """Patch get_region depencency to return a dummy IDP."""
    fake_id = str(uuid.uuid4())

    class FakeRegion:
        id = fake_id

    sub_app_v1.dependency_overrides[get_region] = (
        lambda region_id, session=None: FakeRegion()
    )

    return fake_id


def fake_add_overrides() -> str:
    """Patch get_region depencency to return a dummy IDP."""

    class FakeOverrides(SQLModel): ...

    return FakeOverrides()


# OPTIONS endpoint
def test_options_rels_parent_provider_not_found(client):
    """Test OPTIONS returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_project_id = get_fake_project_id()

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.options(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_options_rels_parent_project_not_found(client):
    """Test OPTIONS returns 404 if parent_project is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_project] = lambda project_id, session=None: None

    resp = client.options(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_options_rels(client):
    """Test OPTIONS returns 204 and Allow header."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()

    resp = client.options(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/"
    )
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


# POST endpoint
def test_create_rel_parent_provider_not_found(client):
    """Test POST returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_project_id = get_fake_project_id()
    fake_region_id = str(uuid.uuid4())
    overrides = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }
    rel_data = {"region_id": fake_region_id, "overrides": overrides}

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions",
        json=rel_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_create_rel_parent_project_not_found(client):
    """Test POST returns 404 if parent_project is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = str(uuid.uuid4())
    fake_region_id = str(uuid.uuid4())
    overrides = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }
    rel_data = {"region_id": fake_region_id, "overrides": overrides}

    sub_app_v1.dependency_overrides[get_project] = lambda project_id, session=None: None

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/",
        json=rel_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_create_rel_target_region_not_found(client):
    """Test POST returns 404 if parent_project is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = str(uuid.uuid4())
    overrides = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }
    rel_data = {"region_id": fake_region_id, "overrides": overrides}

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions",
        json=rel_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_create_rel_success(client, monkeypatch):
    """Test POST /regions/ creates an identity project and returns 201 with id."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = str(uuid.uuid4())
    overrides = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }
    rel_data = {"region_id": fake_region_id, "overrides": overrides}

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.regions.endpoints.connect_project_region",
        lambda session, created_by, project, config: fake_add_overrides(),
    )

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions",
        json=rel_data,
    )
    assert resp.status_code == 201
    assert resp.json() is None


# def test_create_rel_conflict(client, monkeypatch):
#     """Test POST returns 409 if relationship already exists."""
#     fake_provider_id = get_fake_provider_id()
#     fake_project_id = get_fake_project_id()
#     fake_region_id = str(uuid.uuid4())
#     overrides = {
#         "name": DUMMY_NAME,
#         "groups_claim": DUMMY_CLAIM,
#         "protocol": DUMMY_PROTOCOL,
#         "audience": DUMMY_AUD,
#     }
#     rel_data = {"region_id": fake_region_id, "overrides": overrides}

#     def fake_add_region(session, region, project, overrides, created_by):
#         raise ConflictError("Project IDP Connection already exists")

#     monkeypatch.setattr(
#         "fed_mgr.v1.providers.projects.regions.endpoints.add_project_config",
#         fake_add_region,
#     )

#     resp = client.post(
#         f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/",
#         json=rel_data,
#     )
#     assert resp.status_code == 409
#     assert resp.json()["detail"] == "Project IDP Connection already exists"


# def test_create_rel_not_null_error(client, monkeypatch):
#     """Test POST /regions/ returns 409 if a not null error occurs."""
#     fake_provider_id = get_fake_provider_id()
#     fake_project_id = get_fake_project_id()
#     fake_region_id = get_fake_region_id()
#     overrides = {
#         "name": DUMMY_NAME,
#         "groups_claim": DUMMY_CLAIM,
#         "protocol": DUMMY_PROTOCOL,
#         "audience": DUMMY_AUD,
#     }
#     rel_data = {"region_id": fake_region_id, "overrides": overrides}

#     def fake_add_region(session, region, project, overrides, created_by):
#         raise NotNullError("Field 'name' can't be NULL")

#     monkeypatch.setattr(
#         "fed_mgr.v1.providers.projects.regions.endpoints.add_project_config",
#         fake_add_region,
#     )

#     resp = client.post(
#         f"/api/v1/providers/{fake_provider_id}/projects/
# {fake_project_id}/regions/{fake_region_id}",
#         json=rel_data,
#     )
#     assert resp.status_code == 422
#     assert "can't be NULL" in resp.json()["detail"]


# GET (list) endpoint
def test_get_rels_parent_provider_not_found(client):
    """Test GET returns 404 if parent_region is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_project_id = get_fake_project_id()

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_rels_parent_project_not_found(client):
    """Test GET returns 404 if parent_region is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_project] = lambda project_id, session=None: None

    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_rels_success(client, monkeypatch):
    """Test GET /projects/{project_id}/regions/ returns paginated relationships list."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_regions = []
    fake_total = 0

    def fake_get_rels(session, skip, limit, sort, **kwargs):
        return fake_regions, fake_total

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.regions.endpoints.get_region_overrides_list",
        fake_get_rels,
    )
    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()


# GET (by id) endpoint
def test_get_rel_parent_provider_not_found(client):
    """Test GET by id returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda project_id, session=None: None
    )
    sub_app_v1.dependency_overrides[get_region_overrides] = (
        lambda project_id, region_id, session=None: None
    )

    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_rel_parent_project_not_found(client):
    """Test GET by id returns 404 if parent_region is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = str(uuid.uuid4())
    fake_region_id = get_fake_region_id()

    sub_app_v1.dependency_overrides[get_project] = lambda project_id, session=None: None
    sub_app_v1.dependency_overrides[get_region_overrides] = (
        lambda project_id, region_id, session=None: None
    )

    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_rel_target_region_not_found(client):
    """Test GET by id returns 404 if parent_region is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_region] = lambda region_id, session=None: None
    sub_app_v1.dependency_overrides[get_region_overrides] = (
        lambda project_id, region_id, session=None: None
    )

    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_rel_success(client):
    """Test GET returns target rel if found."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()
    fake_id = str(uuid.uuid4())

    class FakeProvRegionRel(SQLModel):
        region_id: uuid.UUID = fake_region_id
        project_id: uuid.UUID = fake_project_id
        name: str = DUMMY_NAME
        groups_claim: str = DUMMY_CLAIM
        protocol: str = DUMMY_PROTOCOL
        audience: str = DUMMY_AUD
        created_at: datetime = DUMMY_CREATED_AT
        created_by_id: uuid.UUID = fake_id
        updated_at: datetime = DUMMY_CREATED_AT
        updated_by_id: uuid.UUID = fake_id

    def fake_get_rel(region_id, project_id, session=None):
        return FakeProvRegionRel()

    sub_app_v1.dependency_overrides[get_region_overrides] = fake_get_rel

    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["region_id"] == fake_region_id


def test_get_rel_not_found(client):
    """Test GET /projects/{project_id}/regions/{region_id} returns 404 if not found."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()

    sub_app_v1.dependency_overrides[get_region_overrides] = (
        lambda region_id, session=None: None
    )

    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 404
    assert (
        resp.json()["detail"]
        == f"Project with ID '{fake_project_id}' does not define overrides for "
        f"region with ID '{fake_region_id}'"
    )


# PUT endpoint
def test_edit_rel_parent_provider_not_found(client):
    """Test PUT returns 404 if paret_project is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}",
        json=rel_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_rel_parent_project_not_found(client):
    """Test PUT returns 404 if paret_project is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = str(uuid.uuid4())
    fake_region_id = get_fake_region_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    sub_app_v1.dependency_overrides[get_project] = lambda project_id, session=None: None

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}",
        json=rel_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_rel_parent_region_not_found(client):
    """Test PUT returns 404 if paret_project is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = str(uuid.uuid4())
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    sub_app_v1.dependency_overrides[get_region] = lambda region_id, session=None: None

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}",
        json=rel_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_rel_success(client, monkeypatch):
    """Test PUT /regions/{region_id} returns 204 on successful update."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_rel(session, region_id, project_id, new_overrides, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.regions.endpoints.update_region_overrides",
        fake_update_rel,
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}",
        json=rel_data,
    )
    assert resp.status_code == 204


def test_edit_region_not_found(client, monkeypatch):
    """Test PUT /regions/{region_id} returns 404 if not found."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_rel(session, region_id, project_id, new_overrides, updated_by):
        raise ItemNotFoundError("Region", id=region_id)

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.regions.endpoints.update_region_overrides",
        fake_update_rel,
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}",
        json=rel_data,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == f"Region with ID '{fake_region_id}' does not exist"


def test_edit_region_conflict(client, monkeypatch):
    """Test PUT /regions/{region_id} returns 409 if conflict error occurs."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_rel(session, region_id, project_id, new_overrides, updated_by):
        raise ConflictError("Region overrides", "name", DUMMY_NAME)

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.regions.endpoints.update_region_overrides",
        fake_update_rel,
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}",
        json=rel_data,
    )
    assert resp.status_code == 409
    assert (
        resp.json()["detail"]
        == f"Region overrides with name={DUMMY_NAME} already exists"
    )


def test_edit_region_not_null_error(client, monkeypatch):
    """Test PUT /regions/{region_id} returns 422 if not null error occurs."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_rel(session, region_id, project_id, new_overrides, updated_by):
        raise NotNullError("Region overrides", "endpoint")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.regions.endpoints.update_region_overrides",
        fake_update_rel,
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}",
        json=rel_data,
    )
    assert resp.status_code == 422
    assert "can't be NULL" in resp.json()["detail"]


# DELETE endpoint
def test_delete_rel_parent_provider_not_found(client):
    """Test DELETE returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.delete(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_delete_rel_parent_project_not_found(client):
    """Test DELETE returns 404 if parent_project is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = str(uuid.uuid4())
    fake_region_id = get_fake_region_id()

    sub_app_v1.dependency_overrides[get_project] = lambda project_id, session=None: None

    resp = client.delete(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_delete_rel_parent_region_not_found(client):
    """Test DELETE returns 404 if parent_region is None."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = str(uuid.uuid4())

    resp = client.delete(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 204


def test_delete_rel_success(client, monkeypatch):
    """Test DELETE /projects/{project_id}/regions/{region_id} returns 204 on success."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.regions.endpoints.disconnect_project_region",
        lambda session, project_id, region_id: None,
    )
    resp = client.delete(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 204


def test_delete_rel_fail(client, monkeypatch):
    """Test DELETE /projects/{project_id}/regions/{region_id} returns 400 on fail."""
    fake_provider_id = get_fake_provider_id()
    fake_project_id = get_fake_project_id()
    fake_region_id = get_fake_region_id()

    def fake_delete_rel(session, project_id, region_id):
        raise DeleteFailedError("Failed to delete item")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.projects.regions.endpoints.disconnect_project_region",
        fake_delete_rel,
    )

    resp = client.delete(
        f"/api/v1/providers/{fake_provider_id}/projects/{fake_project_id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 400
