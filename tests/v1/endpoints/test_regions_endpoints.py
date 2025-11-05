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
from unittest.mock import patch

from fed_mgr.exceptions import ConflictError, DeleteFailedError, ItemNotFoundError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.models import Region
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.regions.crud import get_region
from fed_mgr.v1.providers.regions.schemas import RegionCreate
from fed_mgr.v1.schemas import ItemID


# OPTIONS endpoint
def test_options_regions_parent_provider_not_found(client):
    """Test OPTIONS returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.options(f"/api/v1/providers/{fake_provider_id}/regions/")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_options_regions(client, provider_dep):
    """Test OPTIONS /providers/{provider_id}/regions/ returns 204 and Allow header."""
    resp = client.options(f"/api/v1/providers/{provider_dep.id}/regions/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


# POST endpoint
def test_create_region_parent_provider_not_found(client, region_data):
    """Test POST returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/regions/", json=region_data
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_create_region_success(
    client, session, current_user, provider_dep, region_data
):
    """Test POST /regions/ creates a region and returns 201 with id."""
    fake_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.regions.endpoints.add_region",
        return_value=ItemID(id=fake_id),
    ) as mock_create:
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/regions/", json=region_data
        )
        mock_create.assert_called_once_with(
            session=session,
            region=RegionCreate(**region_data),
            created_by=current_user,
            provider=provider_dep,
        )
        assert resp.status_code == 201
        assert resp.json() == {"id": str(fake_id)}


def test_create_region_conflict(
    client, session, current_user, provider_dep, region_data
):
    """Test POST /regions/ returns 409 if region already exists."""
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.providers.regions.endpoints.add_region",
        side_effect=ConflictError(err_msg),
    ) as mock_create:
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/regions/", json=region_data
        )
        mock_create.assert_called_once_with(
            session=session,
            region=RegionCreate(**region_data),
            created_by=current_user,
            provider=provider_dep,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


# GET (list) endpoint
def test_get_regions_parent_provider_not_found(client):
    """Test GET returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/regions/")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_get_regions_success(client, session, provider_dep, region_data):
    """Test GET /regions/ returns paginated region list."""
    with patch(
        "fed_mgr.v1.providers.regions.endpoints.get_regions",
        return_value=([], 0),
    ) as mock_get:
        resp = client.get(f"/api/v1/providers/{provider_dep.id}/regions/")
        mock_get.assert_called_once_with(
            session=session,
            skip=0,
            limit=5,
            sort="-created_at",
            provider_id=provider_dep.id,
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 0
        assert "page" in resp.json()
        assert "links" in resp.json()

    fake_id = uuid.uuid4()
    user_id = uuid.uuid4()
    region1 = Region(
        **region_data,
        id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
        provider_id=provider_dep.id,
    )
    with patch(
        "fed_mgr.v1.providers.regions.endpoints.get_regions",
        return_value=([region1], 1),
    ) as mock_get:
        resp = client.get(f"/api/v1/providers/{provider_dep.id}/regions/")
        mock_get.assert_called_once_with(
            session=session,
            skip=0,
            limit=5,
            sort="-created_at",
            provider_id=provider_dep.id,
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 1
        assert "page" in resp.json()
        assert "links" in resp.json()

    region2 = Region(
        **region_data,
        id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
        provider_id=provider_dep.id,
    )
    with patch(
        "fed_mgr.v1.providers.regions.endpoints.get_regions",
        return_value=([region1, region2], 2),
    ) as mock_get:
        resp = client.get(f"/api/v1/providers/{provider_dep.id}/regions/")
        mock_get.assert_called_once_with(
            session=session,
            skip=0,
            limit=5,
            sort="-created_at",
            provider_id=provider_dep.id,
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 2
        assert "page" in resp.json()
        assert "links" in resp.json()


# GET (by id) endpoint
def test_get_region_parent_provider_not_found(client):
    """Test GET by id returns 404 if parent_provider is None."""
    fake_id = uuid.uuid4()
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None
    sub_app_v1.dependency_overrides[get_region] = lambda: None

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_get_region_success(client, provider_dep, region_dep):
    """Test GET by id returns user group."""
    resp = client.get(f"/api/v1/providers/{provider_dep.id}/regions/{region_dep.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(region_dep.id)


def test_get_region_not_found(client, provider_dep):
    """Test GET by id returns 404 if not found."""
    fake_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_region] = lambda: None

    resp = client.get(f"/api/v1/providers/{provider_dep.id}/regions/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert f"Region with ID '{fake_id}' does not exist" == resp.json()["detail"]


# PUT endpoint
def test_edit_region_parent_provider_not_found(client, region_data):
    """Test PUT returns 404 if parent_provider is None."""
    fake_id = uuid.uuid4()
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}", json=region_data
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_edit_region_success(client, session, current_user, provider_dep, region_data):
    """Test PUT returns 204 on success."""
    fake_id = uuid.uuid4()

    with patch(
        "fed_mgr.v1.providers.regions.endpoints.update_region",
        return_value=None,
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/regions/{fake_id}", json=region_data
        )
        mock_edit.assert_called_once_with(
            session=session,
            region_id=fake_id,
            new_region=RegionCreate(**region_data),
            updated_by=current_user,
        )
        assert resp.status_code == 204


def test_edit_region_not_found(
    client, session, current_user, provider_dep, region_data
):
    """Test PUT returns 404 if not found."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.providers.regions.endpoints.update_region",
        side_effect=ItemNotFoundError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/regions/{fake_id}", json=region_data
        )
        mock_edit.assert_called_once_with(
            session=session,
            region_id=fake_id,
            new_region=RegionCreate(**region_data),
            updated_by=current_user,
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert resp.json()["detail"] == err_msg


def test_edit_region_conflict(client, session, current_user, provider_dep, region_data):
    """Test PUT returns 409 if conflict."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.providers.regions.endpoints.update_region",
        side_effect=ConflictError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/regions/{fake_id}", json=region_data
        )
        mock_edit.assert_called_once_with(
            session=session,
            region_id=fake_id,
            new_region=RegionCreate(**region_data),
            updated_by=current_user,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


# DELETE endpoint
def test_delete_region_parent_provider_not_found(client):
    """Test DELETE returns 404 if parent_provider is None."""
    fake_id = uuid.uuid4()
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/regions/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        f"Provider with ID '{fake_provider_id}' does not exist" == resp.json()["detail"]
    )


def test_delete_region_success(client, session, provider_dep):
    """Test DELETE returns 204 on success."""
    fake_id = uuid.uuid4()

    with patch(
        "fed_mgr.v1.providers.regions.endpoints.delete_region",
        return_value=None,
    ) as mock_delete:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/regions/{fake_id}")
        mock_delete.assert_called_once_with(session=session, region_id=fake_id)
        assert resp.status_code == 204


def test_delete_region_fail(client, session, provider_dep):
    """Test DELETE /regions/{region_id} returns 400 on fail."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.providers.regions.endpoints.delete_region",
        side_effect=DeleteFailedError(err_msg),
    ) as mock_delete:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/regions/{fake_id}")
        mock_delete.assert_called_once_with(session=session, region_id=fake_id)
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg
