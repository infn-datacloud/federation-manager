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
from unittest.mock import patch

from fed_mgr.exceptions import ConflictError, DeleteFailedError, ItemNotFoundError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.models import RegionOverrides
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.projects.crud import get_project
from fed_mgr.v1.providers.projects.regions.crud import get_region_overrides
from fed_mgr.v1.providers.projects.regions.schemas import RegionOverridesBase
from fed_mgr.v1.providers.regions.crud import get_region


# OPTIONS endpoint
def test_options_rels_parent_provider_not_found(client, project_dep):
    """Test OPTIONS returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.options(
        f"/api/v1/providers/{fake_provider_id}/projects/{project_dep.id}/regions/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_options_rels_parent_project_not_found(client, provider_dep):
    """Test OPTIONS returns 404 if parent_provider is None."""
    fake_project_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_project] = lambda: None

    resp = client.options(
        f"/api/v1/providers/{provider_dep.id}/projects/{fake_project_id}/regions/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Project with ID '{fake_project_id}' does not exist"
    )


def test_options_rels(client, provider_dep, project_dep):
    """Test OPTIONS returns 204 and Allow header."""
    resp = client.options(
        f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/"
    )
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


# POST endpoint
def test_create_rel_parent_provider_not_found(client, project_dep, reg_overrides_data):
    """Test POST returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    fake_region_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None
    rel_data = {"region_id": str(fake_region_id), "overrides": reg_overrides_data}

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/projects/{project_dep.id}/regions",
        json=rel_data,
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_create_rel_parent_project_not_found(
    client, current_user, provider_dep, reg_overrides_data
):
    """Test POST returns 404 if parent_project is None."""
    fake_project_id = uuid.uuid4()
    fake_region_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_project] = lambda: None
    rel_data = {"region_id": str(fake_region_id), "overrides": reg_overrides_data}

    resp = client.post(
        f"/api/v1/providers/{provider_dep.id}/projects/{fake_project_id}/regions",
        json=rel_data,
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Project with ID '{fake_project_id}' does not exist"
    )


def test_create_rel_target_region_not_found(
    client, session, current_user, provider_dep, project_dep, reg_overrides_data
):
    """Test POST returns 404 if parent_project is None."""
    fake_region_id = uuid.uuid4()
    rel_data = {"region_id": str(fake_region_id), "overrides": reg_overrides_data}

    with patch(
        "fed_mgr.v1.providers.projects.regions.endpoints.get_region", return_value=None
    ) as mock_get_region:
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions",
            json=rel_data,
        )
        mock_get_region.assert_called_once_with(
            session=session, region_id=fake_region_id
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert (
            resp.json()["detail"] == f"Region with ID '{fake_region_id}' does not exist"
        )


def test_create_rel_success(
    client,
    session,
    current_user,
    provider_dep,
    project_dep,
    region_dep,
    reg_overrides_data,
):
    """Test POST /regions/ creates an identity project and returns 201 with id."""
    rel_data = {"region_id": str(region_dep.id), "overrides": reg_overrides_data}
    with (
        patch(
            "fed_mgr.v1.providers.projects.regions.endpoints.get_region",
            return_value=region_dep,
        ) as mock_get,
        patch(
            "fed_mgr.v1.providers.projects.regions.endpoints.connect_project_region",
            return_value=RegionOverrides(**rel_data),
        ) as mock_create,
    ):
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/",
            json=rel_data,
        )
        mock_get.assert_called_once_with(session=session, region_id=region_dep.id)
        mock_create.assert_called_once_with(
            session=session,
            project=project_dep,
            region=region_dep,
            overrides=RegionOverridesBase(**reg_overrides_data),
            created_by=current_user,
        )
        assert resp.status_code == 201
        assert resp.json() is None


def test_create_rel_conflict(
    client,
    session,
    current_user,
    provider_dep,
    project_dep,
    region_dep,
    reg_overrides_data,
):
    """Test POST returns 409 if relationship already exists."""
    err_msg = "Error message"
    rel_data = {"region_id": str(region_dep.id), "overrides": reg_overrides_data}

    with (
        patch(
            "fed_mgr.v1.providers.projects.regions.endpoints.get_region",
            return_value=region_dep,
        ) as mock_get,
        patch(
            "fed_mgr.v1.providers.projects.regions.endpoints.connect_project_region",
            side_effect=ConflictError(err_msg),
        ) as mock_create,
    ):
        resp = client.post(
            f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/",
            json=rel_data,
        )
        mock_get.assert_called_once_with(session=session, region_id=region_dep.id)
        mock_create.assert_called_once_with(
            session=session,
            project=project_dep,
            region=region_dep,
            overrides=RegionOverridesBase(**reg_overrides_data),
            created_by=current_user,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


# GET (list) endpoint
def test_get_rels_parent_provider_not_found(client, project_dep):
    """Test GET returns 404 if parent_region is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{project_dep.id}/regions/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_get_rels_parent_project_not_found(client, provider_dep):
    """Test GET returns 404 if parent_region is None."""
    fake_project_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_project] = lambda: None

    resp = client.get(
        f"/api/v1/providers/{provider_dep.id}/projects/{fake_project_id}/regions/"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Project with ID '{fake_project_id}' does not exist"
    )


def test_get_rels_success(
    client, session, provider_dep, project_dep, reg_overrides_data
):
    """Test GET /providers/{provider_id}/regions/ returns paginated list."""
    with patch(
        "fed_mgr.v1.providers.projects.regions.endpoints.get_region_overrides_list",
        return_value=([], 0),
    ) as mock_get:
        resp = client.get(
            f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/"
        )
        mock_get.assert_called_once_with(
            session=session,
            skip=0,
            limit=5,
            sort="-created_at",
            project_id=project_dep.id,
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 0
        assert "page" in resp.json()
        assert "links" in resp.json()

    fake_id = uuid.uuid4()
    user_id = uuid.uuid4()
    region1 = RegionOverrides(
        **reg_overrides_data,
        region_id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    with patch(
        "fed_mgr.v1.providers.projects.regions.endpoints.get_region_overrides_list",
        return_value=([region1], 1),
    ) as mock_get:
        resp = client.get(
            f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/"
        )
        mock_get.assert_called_once_with(
            session=session,
            skip=0,
            limit=5,
            sort="-created_at",
            project_id=project_dep.id,
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 1
        assert "page" in resp.json()
        assert "links" in resp.json()

    region2 = RegionOverrides(
        **reg_overrides_data,
        region_id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    with patch(
        "fed_mgr.v1.providers.projects.regions.endpoints.get_region_overrides_list",
        return_value=([region1, region2], 2),
    ) as mock_get:
        resp = client.get(
            f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/"
        )
        mock_get.assert_called_once_with(
            session=session,
            skip=0,
            limit=5,
            sort="-created_at",
            project_id=project_dep.id,
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 2
        assert "page" in resp.json()
        assert "links" in resp.json()


# GET (by id) endpoint
def test_get_rel_parent_provider_not_found(client, project_dep, region_dep):
    """Test GET by id returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.get(
        f"/api/v1/providers/{fake_provider_id}/projects/{project_dep.id}/regions/{region_dep.id}"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_get_rel_parent_project_not_found(client, provider_dep, region_dep):
    """Test GET by id returns 404 if parent_region is None."""
    fake_project_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_project] = lambda: None

    resp = client.get(
        f"/api/v1/providers/{provider_dep.id}/projects/{fake_project_id}/regions/{region_dep.id}"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Project with ID '{fake_project_id}' does not exist"
    )


def test_get_rel_target_region_not_found(client, provider_dep, project_dep):
    """Test GET by id returns 404 if parent_region is None."""
    fake_region_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_region] = lambda: None

    resp = client.get(
        f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/{fake_region_id}"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert resp.json()["detail"] == f"Region with ID '{fake_region_id}' does not exist"


def test_get_rel_success(
    client, provider_dep, project_dep, region_dep, reg_overrides_dep
):
    """Test GET returns target rel if found."""
    reg_overrides_dep.region_id = region_dep.id
    resp = client.get(
        f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/{region_dep.id}"
    )
    assert resp.status_code == 200
    assert resp.json()["region_id"] == str(reg_overrides_dep.region_id)


def test_get_rel_not_found(client, provider_dep, project_dep, region_dep):
    """Test GET /projects/{project_id}/regions/{region_id} returns 404 if not found."""
    sub_app_v1.dependency_overrides[get_region_overrides] = lambda: None

    resp = client.get(
        f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/{region_dep.id}"
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Project with ID '{project_dep.id}' does not define overrides "
        f"for region with ID '{region_dep.id}'"
    )


# PUT endpoint
def test_edit_rel_parent_provider_not_found(
    client, project_dep, region_dep, reg_overrides_data
):
    """Test PUT returns 404 if paret_project is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/projects/{project_dep.id}/regions/{region_dep.id}",
        json=reg_overrides_data,
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_edit_rel_project_or_region_not_found(
    client, session, current_user, provider_dep, reg_overrides_data
):
    """Test PUT returns 404 if paret_project is None."""
    fake_project_id = uuid.uuid4()
    fake_region_id = uuid.uuid4()
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.providers.projects.regions.endpoints.update_region_overrides",
        side_effect=ItemNotFoundError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/projects/{fake_project_id}/regions/{fake_region_id}",
            json=reg_overrides_data,
        )
        mock_edit.assert_called_once_with(
            session=session,
            region_id=fake_region_id,
            project_id=fake_project_id,
            new_overrides=RegionOverridesBase(**reg_overrides_data),
            updated_by=current_user,
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert resp.json()["detail"] == err_msg


def test_edit_rel_success(
    client,
    session,
    current_user,
    provider_dep,
    project_dep,
    region_dep,
    reg_overrides_data,
):
    """Test PUT /regions/{region_id} returns 204 on successful update."""
    with patch(
        "fed_mgr.v1.providers.projects.regions.endpoints.update_region_overrides",
        return_value=None,
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/{region_dep.id}",
            json=reg_overrides_data,
        )
        mock_edit.assert_called_once_with(
            session=session,
            region_id=region_dep.id,
            project_id=project_dep.id,
            new_overrides=RegionOverridesBase(**reg_overrides_data),
            updated_by=current_user,
        )
        assert resp.status_code == 204


def test_edit_overrides_not_found(
    client,
    session,
    current_user,
    provider_dep,
    project_dep,
    region_dep,
    reg_overrides_data,
):
    """Test PUT /regions/{region_id} returns 404 if not found."""
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.providers.projects.regions.endpoints.update_region_overrides",
        side_effect=ItemNotFoundError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/{region_dep.id}",
            json=reg_overrides_data,
        )
        mock_edit.assert_called_once_with(
            session=session,
            region_id=region_dep.id,
            project_id=project_dep.id,
            new_overrides=RegionOverridesBase(**reg_overrides_data),
            updated_by=current_user,
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert resp.json()["detail"] == err_msg


# DELETE endpoint
def test_delete_rel_parent_provider_not_found(client, project_dep, region_dep):
    """Test DELETE returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.delete(
        f"/api/v1/providers/{fake_provider_id}/projects/{project_dep.id}/regions/{region_dep.id}",
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_delete_rel_success(client, session, provider_dep):
    """Test DELETE /projects/{project_id}/regions/{region_id} returns 204 on success."""
    fake_project_id = uuid.uuid4()
    fake_region_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.projects.regions.endpoints.disconnect_project_region",
        return_value=None,
    ) as mock_delete:
        resp = client.delete(
            f"/api/v1/providers/{provider_dep.id}/projects/{fake_project_id}/regions/{fake_region_id}"
        )
        mock_delete.assert_called_once_with(
            session=session, region_id=fake_region_id, project_id=fake_project_id
        )
        assert resp.status_code == 204


def test_delete_rel_fail(client, session, provider_dep, project_dep, region_dep):
    """Test DELETE /projects/{project_id}/regions/{region_id} returns 400 on fail."""
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.providers.projects.regions.endpoints.disconnect_project_region",
        side_effect=DeleteFailedError(err_msg),
    ) as mock_delete:
        resp = client.delete(
            f"/api/v1/providers/{provider_dep.id}/projects/{project_dep.id}/regions/{region_dep.id}"
        )
        mock_delete.assert_called_once_with(
            session=session, region_id=region_dep.id, project_id=project_dep.id
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg
