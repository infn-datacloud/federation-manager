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

from fed_mgr.exceptions import ConflictError, NoItemToUpdateError, NotNullError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.users.crud import get_current_user


def test_options_idps(client):
    """Test OPTIONS /idps/ returns 204 and Allow header."""
    resp = client.options("/api/v1/idps/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_idp_success(client, monkeypatch):
    """Test POST /idps/ creates an identity provider and returns 201 with id."""
    fake_id = str(uuid.uuid4())

    class FakeIdp:
        id = fake_id

    def fake_add_idp(session, idp, created_by):
        return FakeIdp()

    monkeypatch.setattr("fed_mgr.v1.identity_providers.endpoints.add_idp", fake_add_idp)

    fake_user_info = {"sub": "fake_sub", "iss": "fake_iss"}

    class FakeUserInfos:
        user_info = fake_user_info

    def fake_auth_dep():
        return FakeUserInfos()

    sub_app_v1.dependency_overrides[get_current_user] = fake_auth_dep

    idp_data = {
        "description": "desc",
        "endpoint": "https://idp.example.com",
        "name": "Test IdP",
        "groups_claim": "groups",
        "protocol": "openid",
        "audience": "aud1",
    }
    resp = client.post("/api/v1/idps/", json=idp_data)
    assert resp.status_code == 201
    assert resp.json() == {"id": fake_id}


def test_create_idp_conflict(client, monkeypatch):
    """Test POST /idps/ returns 409 if identity provider already exists."""

    def fake_add_idp(session, idp, created_by):
        raise ConflictError("IDP already exists")

    monkeypatch.setattr("fed_mgr.v1.identity_providers.endpoints.add_idp", fake_add_idp)

    fake_user_info = {"sub": "fake_sub", "iss": "fake_iss"}

    class FakeUserInfos:
        user_info = fake_user_info

    def fake_auth_dep():
        return FakeUserInfos()

    sub_app_v1.dependency_overrides[get_current_user] = fake_auth_dep

    idp_data = {
        "description": "desc",
        "endpoint": "https://idp.example.com",
        "name": "Test IdP",
        "groups_claim": "groups",
        "protocol": "openid",
        "audience": "aud1",
    }
    resp = client.post("/api/v1/idps/", json=idp_data)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "IDP already exists"


def test_create_idp_not_null_error(client, monkeypatch):
    """Test POST /idps/ returns 409 if a not null error occurs."""

    def fake_add_idp(session, idp, created_by):
        raise NotNullError("Field 'endpoint' cannot be null")

    monkeypatch.setattr("fed_mgr.v1.identity_providers.endpoints.add_idp", fake_add_idp)

    fake_user_info = {"sub": "fake_sub", "iss": "fake_iss"}

    class FakeUserInfos:
        user_info = fake_user_info

    def fake_auth_dep():
        return FakeUserInfos()

    sub_app_v1.dependency_overrides[get_current_user] = fake_auth_dep

    idp_data = {
        "description": "desc",
        "endpoint": "https://idp.example.com",
        "name": "Test IdP",
        "groups_claim": "groups",
        "protocol": "openid",
        "audience": "aud1",
    }
    resp = client.post("/api/v1/idps/", json=idp_data)
    assert resp.status_code == 409
    assert "cannot be null" in resp.json()["detail"]


def test_get_idps_success(client, monkeypatch):
    """Test GET /idps/ returns paginated identity provider list."""
    fake_idps = []
    fake_total = 0

    def fake_get_idps(session, skip, limit, sort, **kwargs):
        return fake_idps, fake_total

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.get_idps", fake_get_idps
    )
    resp = client.get("/api/v1/idps/")
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_get_idp_success(client, monkeypatch):
    """Test GET /idps/{idp_id} returns identity provider if found."""
    fake_id = str(uuid.uuid4())

    class FakeIdp:
        id = fake_id
        description = "desc"
        endpoint = "https://idp.example.com"
        name = "Test IdP"
        groups_claim = "groups"
        protocol = "openid"
        audience = "aud1"
        created_at = "2024-01-01T00:00:00Z"
        created_by = fake_id
        updated_at = "2024-01-01T00:00:00Z"
        updated_by = fake_id

    def fake_get_idp(idp_id, session=None):
        return FakeIdp()

    sub_app_v1.dependency_overrides[get_idp] = fake_get_idp
    resp = client.get(f"/api/v1/idps/{fake_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == fake_id


def test_get_idp_not_found(client, monkeypatch):
    """Test GET /idps/{idp_id} returns 404 if not found."""
    fake_id = str(uuid.uuid4())

    def fake_get_idp(idp_id, session=None):
        return None

    sub_app_v1.dependency_overrides[get_idp] = fake_get_idp
    resp = client.get(f"/api/v1/idps/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_idp_success(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 204 on successful update."""
    fake_id = str(uuid.uuid4())

    def fake_update_idp(session, idp_id, new_idp, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.update_idp", fake_update_idp
    )

    fake_user_info = {"sub": "fake_sub", "iss": "fake_iss"}

    class FakeUserInfos:
        user_info = fake_user_info

    def fake_auth_dep():
        return FakeUserInfos()

    sub_app_v1.dependency_overrides[get_current_user] = fake_auth_dep

    idp_data = {
        "description": "desc",
        "endpoint": "https://idp.example.com",
        "name": "Test IdP",
        "groups_claim": "groups",
        "protocol": "openid",
        "audience": "aud1",
    }
    resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
    assert resp.status_code == 204


def test_edit_idp_not_found(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 404 if not found."""
    fake_id = str(uuid.uuid4())

    def fake_update_idp(session, idp_id, new_idp, updated_by):
        raise NoItemToUpdateError("IDP not found")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.update_idp", fake_update_idp
    )

    fake_user_info = {"sub": "fake_sub", "iss": "fake_iss"}

    class FakeUserInfos:
        user_info = fake_user_info

    def fake_auth_dep():
        return FakeUserInfos()

    sub_app_v1.dependency_overrides[get_current_user] = fake_auth_dep

    idp_data = {
        "description": "desc",
        "endpoint": "https://idp.example.com",
        "name": "Test IdP",
        "groups_claim": "groups",
        "protocol": "openid",
        "audience": "aud1",
    }
    resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "IDP not found"


def test_edit_idp_conflict(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 409 if conflict error occurs."""
    fake_id = str(uuid.uuid4())

    def fake_update_idp(session, idp_id, new_idp, updated_by):
        raise ConflictError("IDP already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.update_idp", fake_update_idp
    )

    fake_user_info = {"sub": "fake_sub", "iss": "fake_iss"}

    class FakeUserInfos:
        user_info = fake_user_info

    def fake_auth_dep():
        return FakeUserInfos()

    sub_app_v1.dependency_overrides[get_current_user] = fake_auth_dep

    idp_data = {
        "description": "desc",
        "endpoint": "https://idp.example.com",
        "name": "Test IdP",
        "groups_claim": "groups",
        "protocol": "openid",
        "audience": "aud1",
    }
    resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "IDP already exists"


def test_edit_idp_not_null_error(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 422 if not null error occurs."""
    fake_id = str(uuid.uuid4())

    def fake_update_idp(session, idp_id, new_idp, updated_by):
        raise NotNullError("Field 'endpoint' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.update_idp", fake_update_idp
    )

    fake_user_info = {"sub": "fake_sub", "iss": "fake_iss"}

    class FakeUserInfos:
        user_info = fake_user_info

    def fake_auth_dep():
        return FakeUserInfos()

    sub_app_v1.dependency_overrides[get_current_user] = fake_auth_dep

    idp_data = {
        "description": "desc",
        "endpoint": "https://idp.example.com",
        "name": "Test IdP",
        "groups_claim": "groups",
        "protocol": "openid",
        "audience": "aud1",
    }
    resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


def test_delete_idp_success(client, monkeypatch):
    """Test DELETE /idps/{idp_id} returns 204 on success."""
    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.delete_idp",
        lambda session, idp_id: None,
    )
    resp = client.delete(f"/api/v1/idps/{fake_id}")
    assert resp.status_code == 204
