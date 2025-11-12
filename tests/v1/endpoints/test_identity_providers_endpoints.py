"""Integration tests for fed_mgr.v1.identity_providers.endpoints.

Tests in this file:
- test_options_idps
- test_create_idp_success
- test_create_idp_conflict
- test_create_idp_not_null_error
- test_get_idps_success
- test_get_idp_success
- test_get_idp_not_found
- test_edit_idp_success
- test_edit_idp_not_found
- test_edit_idp_conflict
- test_edit_idp_not_null_error
- test_delete_idp_success
"""

import uuid
from unittest.mock import patch

from fed_mgr.exceptions import ConflictError, DeleteFailedError, ItemNotFoundError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.identity_providers.schemas import IdentityProviderCreate
from fed_mgr.v1.models import IdentityProvider
from fed_mgr.v1.schemas import ItemID


def test_options_idps(client):
    """Test OPTIONS /idps/ returns 204 and Allow header."""
    resp = client.options("/api/v1/idps/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_idp_success(client, session, current_user, idp_data):
    """Test POST /idps/ creates an identity provider and returns 201 with id."""
    fake_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.add_idp",
        return_value=ItemID(id=fake_id),
    ) as mock_create:
        resp = client.post("/api/v1/idps/", json=idp_data)
        mock_create.assert_called_once_with(
            session=session,
            idp=IdentityProviderCreate(**idp_data),
            created_by=current_user,
        )
        assert resp.status_code == 201
        assert resp.json() == {"id": str(fake_id)}


def test_create_idp_conflict(client, session, current_user, idp_data):
    """Test POST /idps/ returns 409 if identity provider already exists."""
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.add_idp",
        side_effect=ConflictError(err_msg),
    ) as mock_create:
        resp = client.post("/api/v1/idps/", json=idp_data)
        mock_create.assert_called_once_with(
            session=session,
            idp=IdentityProviderCreate(**idp_data),
            created_by=current_user,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


def test_get_idps_success(client, session, idp_data):
    """Test GET /idps/ returns paginated identity provider list."""
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.get_idps", return_value=([], 0)
    ) as mock_get:
        resp = client.get("/api/v1/idps/")
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at"
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 0
        assert "page" in resp.json()
        assert "links" in resp.json()

    fake_id = uuid.uuid4()
    user_id = uuid.uuid4()
    idp1 = IdentityProvider(
        **idp_data, id=fake_id, created_by_id=user_id, updated_by_id=user_id
    )
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.get_idps", return_value=([idp1], 1)
    ) as mock_get:
        resp = client.get("/api/v1/idps/")
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at"
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 1
        assert "page" in resp.json()
        assert "links" in resp.json()

    idp2 = IdentityProvider(
        **idp_data, id=fake_id, created_by_id=user_id, updated_by_id=user_id
    )
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.get_idps",
        return_value=([idp1, idp2], 2),
    ) as mock_get:
        resp = client.get("/api/v1/idps/")
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at"
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 2
        assert "page" in resp.json()
        assert "links" in resp.json()


def test_get_idp_success(client, idp_dep):
    """Test GET /idps/{idp_id} returns identity provider if found."""
    resp = client.get(f"/api/v1/idps/{idp_dep.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(idp_dep.id)


def test_get_idp_not_found(client):
    """Test GET /idps/{idp_id} returns 404 if not found."""
    fake_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.get(f"/api/v1/idps/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Identity provider with ID '{fake_id}' does not exist"
    )


def test_edit_idp_success(client, session, current_user, idp_data):
    """Test PUT /idps/{idp_id} returns 204 on successful update."""
    fake_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.update_idp", return_value=None
    ) as mock_edit:
        resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
        mock_edit.assert_called_once_with(
            session=session,
            idp_id=fake_id,
            new_idp=IdentityProviderCreate(**idp_data),
            updated_by=current_user,
        )
        assert resp.status_code == 204


def test_edit_idp_not_found(client, session, current_user, idp_data):
    """Test PUT /idps/{idp_id} returns 404 if not found."""
    fake_id = uuid.uuid4()
    err_msg = "Error err_msg"
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.update_idp",
        side_effect=ItemNotFoundError(err_msg),
    ) as mock_edit:
        resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
        mock_edit.assert_called_once_with(
            session=session,
            idp_id=fake_id,
            new_idp=IdentityProviderCreate(**idp_data),
            updated_by=current_user,
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert resp.json()["detail"] == err_msg


def test_edit_idp_conflict(client, session, current_user, idp_data):
    """Test PUT /idps/{idp_id} returns 409 if conflict error occurs."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.update_idp",
        side_effect=ConflictError(err_msg),
    ) as mock_edit:
        resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
        mock_edit.assert_called_once_with(
            session=session,
            idp_id=fake_id,
            new_idp=IdentityProviderCreate(**idp_data),
            updated_by=current_user,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


def test_delete_idp_success(client, session):
    """Test DELETE /idps/{idp_id} returns 204 on success."""
    fake_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.delete_idp", return_value=None
    ) as mock_delete:
        resp = client.delete(f"/api/v1/idps/{fake_id}")
        mock_delete.assert_called_once_with(session=session, idp_id=fake_id)
        assert resp.status_code == 204


def test_delete_idp_fail(client, session):
    """Test DELETE /idps/{idp_id} returns 400 on fail."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.identity_providers.endpoints.delete_idp",
        side_effect=DeleteFailedError(err_msg),
    ) as mock_delete:
        resp = client.delete(f"/api/v1/idps/{fake_id}")
        mock_delete.assert_called_once_with(session=session, idp_id=fake_id)
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg
