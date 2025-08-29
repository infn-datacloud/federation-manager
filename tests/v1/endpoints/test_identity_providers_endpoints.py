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
from datetime import datetime

from pydantic import AnyHttpUrl
from sqlmodel import SQLModel

from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    ItemNotFoundError,
    NotNullError,
)
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.identity_providers.crud import get_idp

DUMMY_DESC = "desc"
DUMMY_ENDPOINT = "https://idp.example.com"
DUMMY_NAME = "Test IdP"
DUMMY_CLAIM = "groups"
DUMMY_PROTOCOL = "openid"
DUMMY_AUD = "aud1"
DUMMY_CREATED_AT = datetime.now()


def fake_add_idp(fake_id):
    """Return a fake identity provider object with the given id."""

    class FakeIdp(SQLModel):
        id: uuid.UUID = fake_id

    return FakeIdp()


def test_options_idps(client):
    """Test OPTIONS /idps/ returns 204 and Allow header."""
    resp = client.options("/api/v1/idps/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_idp_success(client, monkeypatch):
    """Test POST /idps/ creates an identity provider and returns 201 with id."""
    fake_id = str(uuid.uuid4())
    idp_data = {
        "description": DUMMY_DESC,
        "endpoint": DUMMY_ENDPOINT,
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.add_idp",
        lambda session, idp, created_by: fake_add_idp(fake_id),
    )

    resp = client.post("/api/v1/idps/", json=idp_data)
    assert resp.status_code == 201
    assert resp.json() == {"id": fake_id}


def test_create_idp_conflict(client, monkeypatch):
    """Test POST /idps/ returns 409 if identity provider already exists."""
    idp_data = {
        "description": DUMMY_DESC,
        "endpoint": DUMMY_ENDPOINT,
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_add_idp(session, idp, created_by):
        raise ConflictError("Identity provider", "endpoint", "https://example.com")

    monkeypatch.setattr("fed_mgr.v1.identity_providers.endpoints.add_idp", fake_add_idp)

    resp = client.post("/api/v1/idps/", json=idp_data)
    assert resp.status_code == 409
    assert (
        resp.json()["detail"]
        == "Identity provider with endpoint=https://example.com already exists"
    )


def test_create_idp_not_null_error(client, monkeypatch):
    """Test POST /idps/ returns 409 if a not null error occurs."""
    idp_data = {
        "description": DUMMY_DESC,
        "endpoint": DUMMY_ENDPOINT,
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_add_idp(session, idp, created_by):
        raise NotNullError("Identity provider", "endpoint")

    monkeypatch.setattr("fed_mgr.v1.identity_providers.endpoints.add_idp", fake_add_idp)

    resp = client.post("/api/v1/idps/", json=idp_data)
    assert resp.status_code == 422
    assert "can't be NULL" in resp.json()["detail"]


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


def test_get_idp_success(client):
    """Test GET /idps/{idp_id} returns identity provider if found."""
    fake_id = str(uuid.uuid4())

    class FakeIdp(SQLModel):
        id: uuid.UUID = fake_id
        description: str = DUMMY_DESC
        endpoint: AnyHttpUrl = DUMMY_ENDPOINT
        name: str = DUMMY_NAME
        groups_claim: str = DUMMY_CLAIM
        protocol: str = DUMMY_PROTOCOL
        audience: str = DUMMY_AUD
        created_at: datetime = DUMMY_CREATED_AT
        created_by_id: uuid.UUID = fake_id
        updated_at: datetime = DUMMY_CREATED_AT
        updated_by_id: uuid.UUID = fake_id

    def fake_get_idp(idp_id, session=None):
        return FakeIdp()

    sub_app_v1.dependency_overrides[get_idp] = fake_get_idp

    resp = client.get(f"/api/v1/idps/{fake_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == fake_id


def test_get_idp_not_found(client):
    """Test GET /idps/{idp_id} returns 404 if not found."""
    fake_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None

    resp = client.get(f"/api/v1/idps/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_idp_success(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 204 on successful update."""
    fake_id = str(uuid.uuid4())
    idp_data = {
        "description": DUMMY_DESC,
        "endpoint": DUMMY_ENDPOINT,
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_idp(session, idp_id, new_idp, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.update_idp", fake_update_idp
    )

    resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
    assert resp.status_code == 204


def test_edit_idp_not_found(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 404 if not found."""
    fake_id = str(uuid.uuid4())
    idp_data = {
        "description": DUMMY_DESC,
        "endpoint": DUMMY_ENDPOINT,
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_idp(session, idp_id, new_idp, updated_by):
        raise ItemNotFoundError("Identity provider", id=idp_id)

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.update_idp", fake_update_idp
    )

    resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
    assert resp.status_code == 404
    assert (
        resp.json()["detail"] == f"Identity provider with ID '{fake_id}' does not exist"
    )


def test_edit_idp_conflict(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 409 if conflict error occurs."""
    fake_id = str(uuid.uuid4())
    idp_data = {
        "description": DUMMY_DESC,
        "endpoint": DUMMY_ENDPOINT,
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_idp(session, idp_id, new_idp, updated_by):
        raise ConflictError("Identity Provider", "endpoint", DUMMY_ENDPOINT)

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.update_idp", fake_update_idp
    )

    resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
    assert resp.status_code == 409
    assert (
        resp.json()["detail"]
        == f"Identity Provider with endpoint={DUMMY_ENDPOINT} already exists"
    )


def test_edit_idp_not_null_error(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 422 if not null error occurs."""
    fake_id = str(uuid.uuid4())
    idp_data = {
        "description": DUMMY_DESC,
        "endpoint": DUMMY_ENDPOINT,
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_idp(session, idp_id, new_idp, updated_by):
        raise NotNullError("Identity provider", "endpoint")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.update_idp", fake_update_idp
    )

    resp = client.put(f"/api/v1/idps/{fake_id}", json=idp_data)
    assert resp.status_code == 422
    assert (
        resp.json()["detail"]
        == "Attribute 'endpoint' of Identity provider can't be NULL"
    )


def test_delete_idp_success(client, monkeypatch):
    """Test DELETE /idps/{idp_id} returns 204 on success."""
    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.delete_idp",
        lambda session, idp_id: None,
    )
    resp = client.delete(f"/api/v1/idps/{fake_id}")
    assert resp.status_code == 204


def test_delete_idp_fail(client, monkeypatch):
    """Test DELETE /idps/{idp_id} returns 400 on fail."""
    fake_id = str(uuid.uuid4())

    def fake_delete_idp(session, idp_id):
        raise DeleteFailedError("Failed to delete item")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.endpoints.delete_idp", fake_delete_idp
    )

    resp = client.delete(f"/api/v1/idps/{fake_id}")
    assert resp.status_code == 400
