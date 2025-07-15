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

from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    NoItemToUpdateError,
    NotNullError,
)
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.identity_providers.crud import get_prov_idp_link

DUMMY_ENDPOINT = "https://idp.example.com"
DUMMY_NAME = "Test IdP"
DUMMY_CLAIM = "groups"
DUMMY_PROTOCOL = "openid"
DUMMY_AUD = "aud1"
DUMMY_CREATED_AT = "2024-01-01T00:00:00Z"


def get_fake_provider_id() -> str:
    """Patch get_provider depencency to return a dummy Provider."""
    fake_id = str(uuid.uuid4())

    class FakeProvider:
        id = fake_id

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: FakeProvider()
    )

    return fake_id


def get_fake_idp_id() -> str:
    """Patch get_idp depencency to return a dummy IDP."""
    fake_id = str(uuid.uuid4())

    class FakeIdp:
        id = fake_id

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: FakeIdp()

    return fake_id


# OPTIONS endpoint
def test_options_rels_parent_provider_not_found(client):
    """Test OPTIONS returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.options(f"/api/v1/providers/{fake_provider_id}/idps/")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_options_rels(client):
    """Test OPTIONS /providers/{provider_id}/idps/ returns 204 and Allow header."""
    fake_provider_id = get_fake_provider_id()

    resp = client.options(f"/api/v1/providers/{fake_provider_id}/idps/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


# POST endpoint
def test_create_rel_parent_provider_not_found(client):
    """Test POST returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_create_rel_target_idp_not_found(client):
    """Test POST returns 404 if parent_provider is None."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = str(uuid.uuid4())
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_create_rel_success(client, monkeypatch):
    """Test POST /idps/ creates an identity provider and returns 201 with id."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.connect_prov_idp",
        lambda session, idp, provider, overrides, created_by: None,
    )

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 201
    assert resp.json() is None


def test_create_rel_conflict(client, monkeypatch):
    """Test POST returns 409 if relationship already exists."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_add_idp(session, idp, provider, overrides, created_by):
        raise ConflictError("Provider IDP Connection already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.connect_prov_idp",
        fake_add_idp,
    )

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Provider IDP Connection already exists"


def test_create_rel_not_null_error(client, monkeypatch):
    """Test POST /idps/ returns 409 if a not null error occurs."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_add_idp(session, idp, provider, overrides, created_by):
        raise NotNullError("Field 'name' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.connect_prov_idp",
        fake_add_idp,
    )

    resp = client.post(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


# GET (list) endpoint
def test_get_rels_parent_provider_not_found(client):
    """Test GET returns 404 if parent_idp is None."""
    fake_provider_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/idps/")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_rels_success(client, monkeypatch):
    """Test GET /providers/{provider_id}/idps/ returns paginated relationships list."""
    fake_provider_id = get_fake_provider_id()
    fake_idps = []
    fake_total = 0

    def fake_get_rels(session, skip, limit, sort, **kwargs):
        return fake_idps, fake_total

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.get_prov_idp_links",
        fake_get_rels,
    )
    resp = client.get(f"/api/v1/providers/{fake_provider_id}/idps/")
    assert resp.status_code == 200
    assert "data" in resp.json()


# GET (by id) endpoint
def test_get_rel_parent_provider_not_found(client):
    """Test GET by id returns 404 if parent_idp is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )
    sub_app_v1.dependency_overrides[get_prov_idp_link] = (
        lambda provider_id, idp_id, session=None: None
    )

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_rel_target_idp_not_found(client):
    """Test GET by id returns 404 if parent_idp is None."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None
    sub_app_v1.dependency_overrides[get_prov_idp_link] = (
        lambda provider_id, idp_id, session=None: None
    )

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_rel_success(client):
    """Test GET /providers/{provider_id}/idps/{idp_id} returns target rel if found."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()
    fake_id = str(uuid.uuid4())

    class FakeProvIdpRel:
        idp_id = fake_idp_id
        provider_id = fake_provider_id
        name = DUMMY_NAME
        groups_claim = DUMMY_CLAIM
        protocol = DUMMY_PROTOCOL
        audience = DUMMY_AUD
        created_at = DUMMY_CREATED_AT
        created_by_id = fake_id
        updated_at = DUMMY_CREATED_AT
        updated_by_id = fake_id

        def model_dump(self):
            return {
                "idp_id": self.idp_id,
                "provider_id": self.provider_id,
                "name": self.name,
                "groups_claim": self.groups_claim,
                "protocol": self.protocol,
                "audience": self.audience,
                "created_at": self.created_at,
                "created_by_id": self.created_by_id,
                "updated_at": self.updated_at,
                "updated_by_id": self.updated_by_id,
            }

    def fake_get_rel(idp_id, provider_id, session=None):
        return FakeProvIdpRel()

    sub_app_v1.dependency_overrides[get_prov_idp_link] = fake_get_rel

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}")
    assert resp.status_code == 200
    assert resp.json()["idp_id"] == fake_idp_id
    assert resp.json()["provider_id"] == fake_provider_id


def test_get_rel_not_found(client):
    """Test GET /providers/{provider_id}/idps/{idp_id} returns 404 if not found."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()

    sub_app_v1.dependency_overrides[get_prov_idp_link] = (
        lambda idp_id, session=None: None
    )

    resp = client.get(f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}")
    assert resp.status_code == 404
    assert "is not trusted by provider" in resp.json()["detail"]


# PUT endpoint
def test_edit_rel_parent_provider_not_found(client):
    """Test PUT returns 404 if paret_provider is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
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
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_rel_parent_idp_not_found(client):
    """Test PUT returns 404 if paret_provider is None."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = str(uuid.uuid4())
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_rel_success(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 204 on successful update."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_rel(session, idp_id, provider_id, new_overrides, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.update_prov_idp_link",
        fake_update_rel,
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 204


def test_edit_idp_not_found(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 404 if not found."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_rel(session, idp_id, provider_id, new_overrides, updated_by):
        raise NoItemToUpdateError("IDP not found")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.update_prov_idp_link",
        fake_update_rel,
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "IDP not found"


def test_edit_idp_conflict(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 409 if conflict error occurs."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_rel(session, idp_id, provider_id, new_overrides, updated_by):
        raise ConflictError("IDP already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.update_prov_idp_link",
        fake_update_rel,
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "IDP already exists"


def test_edit_idp_not_null_error(client, monkeypatch):
    """Test PUT /idps/{idp_id} returns 422 if not null error occurs."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()
    rel_data = {
        "name": DUMMY_NAME,
        "groups_claim": DUMMY_CLAIM,
        "protocol": DUMMY_PROTOCOL,
        "audience": DUMMY_AUD,
    }

    def fake_update_rel(session, idp_id, provider_id, new_overrides, updated_by):
        raise NotNullError("Field 'endpoint' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.update_prov_idp_link",
        fake_update_rel,
    )

    resp = client.put(
        f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}", json=rel_data
    )
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


# DELETE endpoint
def test_delete_rel_parent_provider_not_found(client):
    """Test DELETE returns 404 if parent_provider is None."""
    fake_provider_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_delete_rel_parent_idp_not_found(client):
    """Test DELETE returns 404 if parent_idp is None."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None

    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_delete_rel_success(client, monkeypatch):
    """Test DELETE /providers/{provider_id}/idps/{idp_id} returns 204 on success."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.disconnect_prov_idp",
        lambda session, provider_id, idp_id: None,
    )
    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}")
    assert resp.status_code == 204


def test_delete_rel_fail(client, monkeypatch):
    """Test DELETE /providers/{provider_id}/idps/{idp_id} returns 400 on fail."""
    fake_provider_id = get_fake_provider_id()
    fake_idp_id = get_fake_idp_id()

    def fake_delete_rel(session, provider_id, idp_id):
        raise DeleteFailedError("Failed to delete item")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.identity_providers.endpoints.disconnect_prov_idp",
        fake_delete_rel,
    )

    resp = client.delete(f"/api/v1/providers/{fake_provider_id}/idps/{fake_idp_id}")
    assert resp.status_code == 400
