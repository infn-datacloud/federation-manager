"""Integration tests for fed_mgr.v1.providers.identity_providers.endpoints.

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
from fed_mgr.v1.models import IdpOverrides
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.identity_providers.crud import get_idp_overrides
from fed_mgr.v1.providers.identity_providers.schemas import IdpOverridesBase


# OPTIONS endpoint
def test_options_rels_parent_provider_not_found(client):
    """Test OPTIONS returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.options(f"/api/v1/providers/{fake_provider_id}/idps/")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_options_rels(client, provider_dep):
    """Test OPTIONS /providers/{provider_id}/idps/ returns 204 and Allow header."""
    resp = client.options(f"/api/v1/providers/{provider_dep.id}/idps/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


# POST endpoint
def test_create_rel_parent_provider_not_found(client, current_user, idp_overrides_data):
    """Test POST returns 404 if parent_provider is None."""
    fake_provider_id = uuid.uuid4()
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None
    rel_data = {"idp_id": str(fake_idp_id), "overrides": idp_overrides_data}

    resp = client.post(f"/api/v1/providers/{fake_provider_id}/idps/", json=rel_data)
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_create_rel_target_idp_not_found(
    client, session, current_user, provider_dep, idp_overrides_data
):
    """Test POST returns 404 if parent_provider is None."""
    fake_idp_id = uuid.uuid4()
    rel_data = {"idp_id": str(fake_idp_id), "overrides": idp_overrides_data}

    with patch(
        "fed_mgr.v1.providers.identity_providers.endpoints.get_idp", return_value=None
    ) as mock_get_idp:
        resp = client.post(f"/api/v1/providers/{provider_dep.id}/idps/", json=rel_data)
        mock_get_idp.assert_called_once_with(session=session, idp_id=fake_idp_id)
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert (
            resp.json()["detail"]
            == f"Identity provider with ID '{fake_idp_id}' does not exist"
        )


def test_create_rel_success(
    client, session, current_user, provider_dep, idp_dep, idp_overrides_data
):
    """Test POST /idps/ creates an identity provider and returns 201 with id."""
    rel_data = {"idp_id": str(idp_dep.id), "overrides": idp_overrides_data}
    with (
        patch(
            "fed_mgr.v1.providers.identity_providers.endpoints.get_idp",
            return_value=idp_dep,
        ) as mock_get,
        patch(
            "fed_mgr.v1.providers.identity_providers.endpoints.connect_prov_idp",
            return_value=IdpOverrides(**rel_data),
        ) as mock_create,
    ):
        resp = client.post(f"/api/v1/providers/{provider_dep.id}/idps/", json=rel_data)
        mock_get.assert_called_once_with(session=session, idp_id=idp_dep.id)
        mock_create.assert_called_once_with(
            session=session,
            provider=provider_dep,
            idp=idp_dep,
            overrides=IdpOverridesBase(**idp_overrides_data),
            created_by=current_user,
        )
        assert resp.status_code == 201
        assert resp.json() is None


def test_create_rel_conflict(
    client,
    session,
    current_user,
    provider_dep,
    idp_dep,
    idp_overrides_data,
):
    """Test POST returns 409 if relationship already exists."""
    err_msg = "Error message"
    rel_data = {"idp_id": str(idp_dep.id), "overrides": idp_overrides_data}

    with (
        patch(
            "fed_mgr.v1.providers.identity_providers.endpoints.get_idp",
            return_value=idp_dep,
        ) as mock_get,
        patch(
            "fed_mgr.v1.providers.identity_providers.endpoints.connect_prov_idp",
            side_effect=ConflictError(err_msg),
        ) as mock_create,
    ):
        resp = client.post(f"/api/v1/providers/{provider_dep.id}/idps/", json=rel_data)
        mock_get.assert_called_once_with(session=session, idp_id=idp_dep.id)
        mock_create.assert_called_once_with(
            session=session,
            provider=provider_dep,
            idp=idp_dep,
            overrides=IdpOverridesBase(**idp_overrides_data),
            created_by=current_user,
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg


# GET (list) endpoint
def test_get_rels_parent_provider_not_found(client):
    """Test GET returns 404 if parent_idp is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/idps/")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_get_rels_success(client, session, provider_dep, idp_overrides_data):
    """Test GET /providers/{provider_id}/idps/ returns paginated relationships list."""
    with patch(
        "fed_mgr.v1.providers.identity_providers.endpoints.get_idp_overrides_list",
        return_value=([], 0),
    ) as mock_get:
        resp = client.get(f"/api/v1/providers/{provider_dep.id}/idps/")
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
    idp1 = IdpOverrides(
        **idp_overrides_data,
        idp_id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    with patch(
        "fed_mgr.v1.providers.identity_providers.endpoints.get_idp_overrides_list",
        return_value=([idp1], 1),
    ) as mock_get:
        resp = client.get(f"/api/v1/providers/{provider_dep.id}/idps/")
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

    idp2 = IdpOverrides(
        **idp_overrides_data,
        idp_id=fake_id,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    with patch(
        "fed_mgr.v1.providers.identity_providers.endpoints.get_idp_overrides_list",
        return_value=([idp1, idp2], 2),
    ) as mock_get:
        resp = client.get(f"/api/v1/providers/{provider_dep.id}/idps/")
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
def test_get_rel_parent_provider_not_found(client, idp_dep):
    """Test GET by id returns 404 if parent_idp is None."""
    fake_provider_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_provider] = lambda: None

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/idps/{idp_dep.id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"] == f"Provider with ID '{fake_provider_id}' does not exist"
    )


def test_get_rel_target_idp_not_found(client, provider_dep):
    """Test GET by id returns 404 if parent_idp is None."""
    fake_idp_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[get_idp] = lambda: None

    resp = client.get(f"/api/v1/providers/{provider_dep.id}/idps/{fake_idp_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Identity provider with ID '{fake_idp_id}' does not exist"
    )


def test_get_rel_success(client, provider_dep, idp_dep, idp_overrides_dep):
    """Test GET /providers/{provider_id}/idps/{idp_id} returns target rel if found."""
    idp_overrides_dep.idp_id = idp_dep.id
    resp = client.get(f"/api/v1/providers/{provider_dep.id}/idps/{idp_dep.id}")
    assert resp.status_code == 200
    assert resp.json()["idp_id"] == str(idp_overrides_dep.idp_id)


def test_get_rel_not_found(client, provider_dep, idp_dep):
    """Test GET /providers/{provider_id}/idps/{idp_id} returns 404 if not found."""
    sub_app_v1.dependency_overrides[get_idp_overrides] = lambda: None

    resp = client.get(f"/api/v1/providers/{provider_dep.id}/idps/{idp_dep.id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert (
        resp.json()["detail"]
        == f"Provider with ID '{provider_dep.id}' does not define overrides "
        f"for identity provider with ID '{idp_dep.id}'"
    )


# PUT endpoint
def test_edit_rel_provider_or_idp_not_found(
    client, session, current_user, idp_overrides_data
):
    """Test PUT returns 404 if paret_provider is None."""
    fake_provider_id = uuid.uuid4()
    fake_idp_id = uuid.uuid4()
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.providers.identity_providers.endpoints.update_idp_overrides",
        side_effect=ItemNotFoundError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}",
            json=idp_overrides_data,
        )
        mock_edit.assert_called_once_with(
            session=session,
            idp_id=fake_idp_id,
            provider_id=fake_provider_id,
            new_overrides=IdpOverridesBase(**idp_overrides_data),
            updated_by=current_user,
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert resp.json()["detail"] == err_msg


def test_edit_rel_success(
    client, session, current_user, provider_dep, idp_dep, idp_overrides_data
):
    """Test PUT /idps/{idp_id} returns 204 on successful update."""
    with patch(
        "fed_mgr.v1.providers.identity_providers.endpoints.update_idp_overrides",
        return_value=None,
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/idps/{idp_dep.id}",
            json=idp_overrides_data,
        )
        mock_edit.assert_called_once_with(
            session=session,
            idp_id=idp_dep.id,
            provider_id=provider_dep.id,
            new_overrides=IdpOverridesBase(**idp_overrides_data),
            updated_by=current_user,
        )
        assert resp.status_code == 204


def test_edit_overrides_not_found(
    client, session, current_user, provider_dep, idp_dep, idp_overrides_data
):
    """Test PUT /idps/{idp_id} returns 404 if not found."""
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.providers.identity_providers.endpoints.update_idp_overrides",
        side_effect=ItemNotFoundError(err_msg),
    ) as mock_edit:
        resp = client.put(
            f"/api/v1/providers/{provider_dep.id}/idps/{idp_dep.id}",
            json=idp_overrides_data,
        )
        mock_edit.assert_called_once_with(
            session=session,
            idp_id=idp_dep.id,
            provider_id=provider_dep.id,
            new_overrides=IdpOverridesBase(**idp_overrides_data),
            updated_by=current_user,
        )
        assert resp.status_code == 404
        assert resp.json()["status"] == 404
        assert resp.json()["detail"] == err_msg


# DELETE endpoint
def test_delete_rel_success(client, session):
    """Test DELETE /providers/{provider_id}/idps/{idp_id} returns 204 on success."""
    fake_provider_id = uuid.uuid4()
    fake_idp_id = uuid.uuid4()
    with patch(
        "fed_mgr.v1.providers.identity_providers.endpoints.disconnect_prov_idp",
        return_value=None,
    ) as mock_delete:
        resp = client.delete(f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}")
        mock_delete.assert_called_once_with(
            session=session, idp_id=fake_idp_id, provider_id=fake_provider_id
        )
        assert resp.status_code == 204


def test_delete_rel_fail(client, session, provider_dep, idp_dep):
    """Test DELETE /idps/{idp_id} returns 400 on fail."""
    err_msg = "Error message"
    with patch(
        "fed_mgr.v1.providers.identity_providers.endpoints.disconnect_prov_idp",
        side_effect=DeleteFailedError(err_msg),
    ) as mock_delete:
        resp = client.delete(f"/api/v1/providers/{provider_dep.id}/idps/{idp_dep.id}")
        mock_delete.assert_called_once_with(
            session=session, idp_id=idp_dep.id, provider_id=provider_dep.id
        )
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg
