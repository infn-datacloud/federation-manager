"""Integration tests for fed_mgr.v1.identity_providers.user_groups.endpoints.

Tests in this file:
- test_options_user_groups
- test_create_user_group_success
- test_create_user_group_conflict
- test_create_user_group_not_null_error
- test_create_user_group_parent_idp_not_found
- test_get_user_groups_success
- test_get_user_group_success
- test_get_user_group_not_found
- test_edit_user_group_success
- test_edit_user_group_not_found
- test_edit_user_group_conflict
- test_edit_user_group_not_null_error
- test_delete_user_group_success
"""

import uuid
from unittest.mock import patch

from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    ItemNotFoundError,
)
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.identity_providers.user_groups.crud import get_user_group
from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroupCreate
from fed_mgr.v1.models import UserGroup
from fed_mgr.v1.schemas import ItemID


# OPTIONS endpoint
def test_options_user_groups_parent_idp_not_found(client):
    """Test OPTIONS returns 404 if parent_idp is None."""
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.options(f"/api/v1/idps/{fake_idp_id}/user-groups/")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_options_user_groups(client, idp_dep):
    """Test OPTIONS /idps/{idp_id}/user-groups/ returns 204 and Allow header."""
    resp = client.options(f"/api/v1/idps/{idp_dep.id}/user-groups/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


# POST endpoint
def test_create_user_group_parent_idp_not_found(client, user_group_data):
    """Test POST returns 404 if parent_idp is None."""
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.post(f"/api/v1/idps/{fake_idp_id}/user-groups/", json=user_group_data)
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_create_user_group_success(
    client,
    session,
    current_user,
    user_group_data,
    idp_dep,
):
    """Test POST creates a user group and returns 201 with id."""
    fake_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.add_user_group",
        return_value=ItemID(id=fake_id),
    ) as mock_create:
        resp = client.post(
            f"/api/v1/idps/{idp_dep.id}/user-groups/", json=user_group_data
        )
        mock_create.assert_called_once_with(
            session=session,
            user_group=UserGroupCreate(**user_group_data),
            created_by=current_user,
            idp=idp_dep,
        )
        assert resp.status_code == 201
        assert resp.json() == {"id": str(fake_id)}


def test_create_user_group_conflict(
    client, session, current_user, user_group_data, idp_dep
):
    """Test POST returns 409 if user group already exists."""
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.add_user_group",
        side_effect=ConflictError(err_msg),
    ) as mock_create:
        resp = client.post(
            f"/api/v1/idps/{idp_dep.id}/user-groups/", json=user_group_data
        )
        mock_create.assert_called_once_with(
            session=session,
            user_group=UserGroupCreate(**user_group_data),
            created_by=current_user,
            idp=idp_dep,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


# GET (list) endpoint
def test_get_user_groups_parent_idp_not_found(client):
    """Test GET returns 404 if parent_idp is None."""
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.get(f"/api/v1/idps/{fake_idp_id}/user-groups/")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_get_user_groups_success(client, session, user_group_data, idp_dep):
    """Test GET returns paginated user group list."""
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.get_user_groups",
        return_value=([], 0),
    ) as mock_get:
        resp = client.get(f"/api/v1/idps/{idp_dep.id}/user-groups/")
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at", idp_id=idp_dep.id
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 0
        assert "page" in resp.json()
        assert "links" in resp.json()

    fake_id = uuid.uuid4()
    user_id = uuid.uuid4()
    group1 = UserGroup(
        **user_group_data,
        id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
        idp_id=idp_dep.id,
    )
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.get_user_groups",
        return_value=([group1], 1),
    ) as mock_get:
        resp = client.get(f"/api/v1/idps/{idp_dep.id}/user-groups/")
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at", idp_id=idp_dep.id
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 1
        assert "page" in resp.json()
        assert "links" in resp.json()

    group2 = UserGroup(
        **user_group_data,
        id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
        idp_id=idp_dep.id,
    )
    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.get_user_groups",
        return_value=([group1, group2], 2),
    ) as mock_get:
        resp = client.get(f"/api/v1/idps/{idp_dep.id}/user-groups/")
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at", idp_id=idp_dep.id
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 2
        assert "page" in resp.json()
        assert "links" in resp.json()


# GET (by id) endpoint
def test_get_user_group_parent_idp_not_found(client):
    """Test GET by id returns 404 if parent_idp is None."""
    fake_id = uuid.uuid4()
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None
    sub_app_v1.dependency_overrides[get_user_group] = lambda: None

    resp = client.get(f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_get_user_group_success(client, idp_dep, user_group_dep):
    """Test GET by id returns user group."""
    resp = client.get(f"/api/v1/idps/{idp_dep.id}/user-groups/{user_group_dep.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(user_group_dep.id)


def test_get_user_group_not_found(client, idp_dep):
    """Test GET by id returns 404 if not found."""
    fake_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_user_group] = lambda: None

    resp = client.get(f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert resp.json()["detail"] == f"User group with ID '{fake_id}' does not exist"


# PUT endpoint
def test_edit_user_group_parent_idp_not_found(client, user_group_data):
    """Test PUT returns 404 if parent_idp is None."""
    fake_id = uuid.uuid4()
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_id}", json=user_group_data
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_edit_user_group_success(
    client, session, current_user, idp_dep, user_group_data
):
    """Test PUT returns 204 on success."""
    fake_id = uuid.uuid4()

    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.update_user_group",
        return_value=None,
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_id}", json=user_group_data
        )
        mock_edit.assert_called_once_with(
            session=session,
            user_group_id=fake_id,
            new_user_group=UserGroupCreate(**user_group_data),
            updated_by=current_user,
        )
        assert resp.status_code == 204


def test_edit_user_group_not_found(
    client, session, current_user, idp_dep, user_group_data
):
    """Test PUT returns 404 if not found."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.update_user_group",
        side_effect=ItemNotFoundError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_id}", json=user_group_data
        )
        mock_edit.assert_called_once_with(
            session=session,
            user_group_id=fake_id,
            new_user_group=UserGroupCreate(**user_group_data),
            updated_by=current_user,
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert resp.json()["detail"] == err_msg


def test_edit_user_group_conflict(
    client, session, current_user, idp_dep, user_group_data
):
    """Test PUT returns 409 if conflict."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.update_user_group",
        side_effect=ConflictError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_id}", json=user_group_data
        )
        mock_edit.assert_called_once_with(
            session=session,
            user_group_id=fake_id,
            new_user_group=UserGroupCreate(**user_group_data),
            updated_by=current_user,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


# DELETE endpoint
def test_delete_user_group_parent_idp_not_found(client):
    """Test DELETE returns 404 if parent_idp is None."""
    fake_id = uuid.uuid4()
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.delete(f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_delete_user_group_success(client, session, idp_dep):
    """Test DELETE returns 204 on success."""
    fake_id = uuid.uuid4()

    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.delete_user_group",
        return_value=None,
    ) as mock_delete:
        resp = client.delete(f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_id}")
        mock_delete.assert_called_once_with(session=session, user_group_id=fake_id)
        assert resp.status_code == 204


def test_delete_user_group_fail(client, session, idp_dep):
    """Test DELETE /user_groups/{user_group_id} returns 400 on fail."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"

    with patch(
        "fed_mgr.v1.identity_providers.user_groups.endpoints.delete_user_group",
        side_effect=DeleteFailedError(err_msg),
    ) as mock_delete:
        resp = client.delete(f"/api/v1/idps/{idp_dep.id}/user-groups/{fake_id}")
        mock_delete.assert_called_once_with(session=session, user_group_id=fake_id)
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg
