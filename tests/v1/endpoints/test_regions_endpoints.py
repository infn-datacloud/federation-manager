"""Integration tests for fed_mgr.v1.providers.regions.endpoints.

Tests in this file:
- test_options_regions
- test_create_region_success
- test_create_region_conflict
- test_create_region_not_null_error
- test_create_region_location_not_found
- test_get_regions_success
- test_get_region_success
- test_get_region_not_found
- test_edit_region_success
- test_edit_region_not_found
- test_edit_region_conflict
- test_edit_region_not_null_error
- test_edit_region_location_not_found
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
from fed_mgr.v1.providers.regions.crud import get_region

DUMMY_NAME = "eu-west-1"
DUMMY_DESC = "A test region."
DUMMY_CREATED_AT = datetime.now()
DUMMY_LOCATION_ID = str(uuid.uuid4())


def get_fake_provider_id() -> str:
    """Patch get_idp depencency to return a dummy IDP."""
    fake_id = str(uuid.uuid4())

    class FakeProvider:
        id = fake_id

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: FakeProvider()
    )

    return fake_id


def fake_add_region(fake_id):
    """Return a fake region object with the given id."""

    class FakeRegion(SQLModel):
        id: uuid.UUID = fake_id

    return FakeRegion()


def test_options_regions_parent_provider_not_found(client):
    """Test OPTIONS returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.options(f"/api/v1/providers/{fake_provider_id}/regions/")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_options_regions(client):
    """Test OPTIONS /providers/{provider_id}/regions/ returns 204 and Allow header."""
    fake_provider_id = get_fake_provider_id()

    resp = client.options(f"/api/v1/providers/{fake_provider_id}/regions/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_region_parent_provider_not_found(client):
    """Test POST returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())
    region_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "location_id": DUMMY_LOCATION_ID,
    }

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/regions/", json=region_data
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_create_region_success(client, monkeypatch):
    """Test POST /regions/ creates a region and returns 201 with id."""
    fake_id = str(uuid.uuid4())
    fake_provider_id = get_fake_provider_id()
    region_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "location_id": DUMMY_LOCATION_ID,
    }
    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.add_region",
        lambda session, region, created_by, provider: fake_add_region(fake_id),
    )
    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/regions/", json=region_data
    )
    assert resp.status_code == 201
    assert resp.json() == {"id": fake_id}


def test_create_region_conflict(client, monkeypatch):
    """Test POST /regions/ returns 409 if region already exists."""
    fake_provider_id = get_fake_provider_id()
    region_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "location_id": DUMMY_LOCATION_ID,
    }

    def fake_add_region(session, region, created_by, provider):
        raise ConflictError("Region", "name", DUMMY_NAME)

    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.add_region", fake_add_region
    )
    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/regions/", json=region_data
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == f"Region with name={DUMMY_NAME} already exists"


def test_create_region_not_null_error(client, monkeypatch):
    """Test POST /regions/ returns 422 if a not null error occurs."""
    fake_provider_id = get_fake_provider_id()
    region_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "location_id": DUMMY_LOCATION_ID,
    }

    def fake_add_region(session, region, created_by, provider):
        raise NotNullError("Region", "name")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.add_region", fake_add_region
    )
    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/regions/", json=region_data
    )
    assert resp.status_code == 422
    assert "can't be NULL" in resp.json()["detail"]


# def test_create_region_location_not_found(client, monkeypatch):
#     """Test POST /regions/ returns 400 if location not found."""
#     fake_provider_id = get_fake_provider_id()
#     region_data = {
#         "name": DUMMY_NAME,
#         "description": DUMMY_DESC,
#         "location_id": DUMMY_LOCATION_ID,
#     }

#     def fake_add_region(session, region, created_by, provider):
#         raise LocationNotFoundError("Location not found")

#     monkeypatch.setattr(
#         "fed_mgr.v1.providers.regions.endpoints.add_region", fake_add_region
#     )
#     resp = client.post(
#         f"/api/v1/providers/{fake_provider_id}/regions/", json=region_data
#     )
#     assert resp.status_code == 400
#     assert "Location not found" in resp.json()["detail"]


def test_get_regions_parent_provider_not_found(client):
    """Test GET returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/regions/")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_regions_success(client, monkeypatch):
    """Test GET /regions/ returns paginated region list."""
    fake_provider_id = get_fake_provider_id()
    fake_regions = []
    fake_total = 0

    def fake_get_regions(session, skip, limit, sort, **kwargs):
        return fake_regions, fake_total

    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.get_regions", fake_get_regions
    )
    resp = client.get(f"/api/v1/providers/{fake_provider_id}/regions/")
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_get_region_parent_provider_not_found(client):
    """Test GET by id returns 404 if parent_provider is None."""
    fake_id = str(uuid.uuid4())
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )
    sub_app_v1.dependency_overrides[get_region] = lambda region_id, session=None: None

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_region_success(client):
    """Test GET /regions/{region_id} returns region if found."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())

    class FakeRegion(SQLModel):
        id: uuid.UUID = fake_id
        name: str = DUMMY_NAME
        description: str = DUMMY_DESC
        # location_id: uuid.UUID = DUMMY_LOCATION_ID
        created_at: datetime = DUMMY_CREATED_AT
        created_by_id: uuid.UUID = fake_id
        updated_at: datetime = DUMMY_CREATED_AT
        updated_by_id: uuid.UUID = fake_id

    def fake_get_region(region_id, session=None):
        return FakeRegion()

    sub_app_v1.dependency_overrides[get_region] = fake_get_region
    resp = client.get(f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == fake_id


def test_get_region_not_found(client):
    """Test GET /regions/{region_id} returns 404 if not found."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    sub_app_v1.dependency_overrides[get_region] = lambda region_id, session=None: None
    resp = client.get(f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_region_parent_prpvider_not_found(client):
    """Test PUT returns 404 if parent_provider is None."""
    fake_id = str(uuid.uuid4())
    fake_provider_id = str(uuid.uuid4())
    region_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "location_id": DUMMY_LOCATION_ID,
    }

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}", json=region_data
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_region_success(client, monkeypatch):
    """Test PUT /regions/{region_id} returns 204 on successful update."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    region_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "location_id": DUMMY_LOCATION_ID,
    }

    def fake_update_region(session, region_id, new_region, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.update_region", fake_update_region
    )
    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}", json=region_data
    )
    assert resp.status_code == 204


def test_edit_region_not_found(client, monkeypatch):
    """Test PUT /regions/{region_id} returns 404 if not found."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    region_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "location_id": DUMMY_LOCATION_ID,
    }

    def fake_update_region(session, region_id, new_region, updated_by):
        raise ItemNotFoundError("Region", id=region_id)

    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.update_region", fake_update_region
    )
    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}", json=region_data
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == f"Region with ID '{fake_id}' does not exist"


def test_edit_region_conflict(client, monkeypatch):
    """Test PUT /regions/{region_id} returns 409 if conflict error occurs."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    region_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        # "location_id": DUMMY_LOCATION_ID,
    }

    def fake_update_region(session, region_id, new_region, updated_by):
        raise ConflictError("Region", "name", DUMMY_NAME)

    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.update_region", fake_update_region
    )
    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}", json=region_data
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == f"Region with name={DUMMY_NAME} already exists"


def test_edit_region_not_null_error(client, monkeypatch):
    """Test PUT /regions/{region_id} returns 422 if not null error occurs."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    region_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        # "location_id": DUMMY_LOCATION_ID,
    }

    def fake_update_region(session, region_id, new_region, updated_by):
        raise NotNullError("Region", "name")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.update_region", fake_update_region
    )
    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}", json=region_data
    )
    assert resp.status_code == 422
    assert "can't be NULL" in resp.json()["detail"]


# def test_edit_region_location_not_found(client, monkeypatch):
#     """Test PUT /regions/{region_id} returns 400 if location not found."""
#     fake_provider_id = get_fake_provider_id()
#     fake_id = str(uuid.uuid4())
#     region_data = {
#         "name": DUMMY_NAME,
#         "description": DUMMY_DESC,
#         "location_id": DUMMY_LOCATION_ID,
#     }

#     def fake_update_region(session, region_id, new_region, updated_by):
#         raise LocationNotFoundError("Location not found")

#     monkeypatch.setattr(
#         "fed_mgr.v1.providers.regions.endpoints.update_region", fake_update_region
#     )
#     resp = client.put(
#         f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}", json=region_data
#     )
#     assert resp.status_code == 400
#     assert "Location not found" in resp.json()["detail"]


def test_delete_region_parent_provider_not_found(client):
    """Test DELETE returns 404 if parent_provider is None."""
    fake_id = str(uuid.uuid4())
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_delete_region_success(client, monkeypatch):
    """Test DELETE /regions/{region_id} returns 204 on success."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.delete_region",
        lambda session, region_id: None,
    )
    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}")
    assert resp.status_code == 204


def test_delete_region_fail(client, monkeypatch):
    """Test DELETE /regions/{region_id} returns 400 on fail."""
    fake_provider_id = get_fake_provider_id()
    fake_id = str(uuid.uuid4())

    def fake_delete_region(session, region_id):
        raise DeleteFailedError("Failed to delete item")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.regions.endpoints.delete_region", fake_delete_region
    )

    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}")
    assert resp.status_code == 400
