"""Integration tests for fed_mgr.v1.providers.endpoints.

Tests in this file:
- test_options_providers
- test_create_provider_success
- test_create_provider_conflict
- test_create_provider_not_null_error
- test_get_providers_success
- test_get_provider_success
- test_get_provider_not_found
- test_edit_provider_success
- test_edit_provider_not_found
- test_edit_provider_conflict
- test_edit_provider_not_null_error
- test_delete_provider_success
- test_update_provider_state_success
- test_update_provider_state_forbidden
"""

import uuid
from unittest.mock import MagicMock

from fed_mgr.exceptions import (
    ConflictError,
    NoItemToUpdateError,
    NotNullError,
    ProviderStateChangeError,
)
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.schemas import ProviderStatus

DUMMY_NAME = "foo"
DUMMY_DESC = "desc"
DUMMY_TYPE = "openstack"
DUMMY_AUTH_ENDPOINT = "https://example.com/auth"
DUMMY_IS_PUB = True
DUMMY_EMAILS = ["admin@example.com"]
DUMMY_CREATED_AT = "2024-01-01T00:00:00Z"
DUMMY_ADMINS = [str(uuid.uuid4())]


def fake_add_provider(fake_id):
    """Return a fake resource provider object with the given id."""

    class FakeProvider:
        id = fake_id

    return FakeProvider()


def test_options_providers(client):
    """Test OPTIONS /providers/ returns 204 and Allow header."""
    resp = client.options("/api/v1/providers/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_provider_success(client, monkeypatch):
    """Test POST /providers/ creates an resource provider and returns 201 with id."""
    fake_id = str(uuid.uuid4())
    provider_data = {
        "description": DUMMY_DESC,
        "name": DUMMY_NAME,
        "type": DUMMY_TYPE,
        "auth_endpoint": DUMMY_AUTH_ENDPOINT,
        "is_public": DUMMY_IS_PUB,
        "support_emails": DUMMY_EMAILS,
        "site_admins": DUMMY_ADMINS,
    }

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.add_provider",
        lambda session, provider, created_by: fake_add_provider(fake_id),
    )

    resp = client.post("/api/v1/providers/", json=provider_data)
    assert resp.status_code == 201
    assert resp.json() == {"id": fake_id}


def test_create_provider_conflict(client, monkeypatch):
    """Test POST /providers/ returns 409 if resource provider already exists."""
    provider_data = {
        "description": DUMMY_DESC,
        "name": DUMMY_NAME,
        "type": DUMMY_TYPE,
        "auth_endpoint": DUMMY_AUTH_ENDPOINT,
        "is_public": DUMMY_IS_PUB,
        "support_emails": DUMMY_EMAILS,
        "site_admins": DUMMY_ADMINS,
    }

    def fake_add_provider(session, provider, created_by):
        raise ConflictError("Provider already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.add_provider", fake_add_provider
    )

    resp = client.post("/api/v1/providers/", json=provider_data)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Provider already exists"


def test_create_provider_not_null_error(client, monkeypatch):
    """Test POST /providers/ returns 422 if a not null error occurs."""
    provider_data = {
        "description": DUMMY_DESC,
        "name": DUMMY_NAME,
        "type": DUMMY_TYPE,
        "auth_endpoint": DUMMY_AUTH_ENDPOINT,
        "is_public": DUMMY_IS_PUB,
        "support_emails": DUMMY_EMAILS,
        "site_admins": DUMMY_ADMINS,
    }

    def fake_add_provider(session, provider, created_by):
        raise NotNullError("Field 'endpoint' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.add_provider", fake_add_provider
    )

    resp = client.post("/api/v1/providers/", json=provider_data)
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


def test_get_providers_success(client, monkeypatch):
    """Test GET /providers/ returns paginated resource provider list."""
    fake_providers = []
    fake_total = 0

    def fake_get_providers(session, skip, limit, sort, **kwargs):
        return fake_providers, fake_total

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.get_providers", fake_get_providers
    )
    resp = client.get("/api/v1/providers/")
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_get_provider_success(client):
    """Test GET /providers/{provider_id} returns resource provider if found."""
    fake_id = str(uuid.uuid4())
    site_admin = MagicMock()
    site_admin.id = uuid.uuid4()
    site_admins_ = [site_admin]

    class FakeProvider:
        id = fake_id
        description = DUMMY_DESC
        name = DUMMY_NAME
        type = DUMMY_TYPE
        auth_endpoint = DUMMY_AUTH_ENDPOINT
        is_public = DUMMY_IS_PUB
        support_emails = DUMMY_EMAILS
        site_admins = site_admins_
        created_at = DUMMY_CREATED_AT
        created_by = fake_id
        updated_at = DUMMY_CREATED_AT
        updated_by = fake_id

        def model_dump(self):
            # Does not return site_admins which is a relationship
            return {
                "id": self.id,
                "description": self.description,
                "name": self.name,
                "type": self.type,
                "auth_endpoint": self.auth_endpoint,
                "is_public": self.is_public,
                "support_emails": self.support_emails,
                "status": 0,
                "created_at": self.created_at,
                "created_by": self.created_by,
                "updated_at": self.updated_at,
                "updated_by": self.updated_by,
            }

    def fake_get_provider(provider_id, session=None):
        return FakeProvider()

    sub_app_v1.dependency_overrides[get_provider] = fake_get_provider

    resp = client.get(f"/api/v1/providers/{fake_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == fake_id


def test_get_provider_not_found(client):
    """Test GET /providers/{provider_id} returns 404 if not found."""
    fake_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_provider] = (
        lambda provider_id, session=None: None
    )

    resp = client.get(f"/api/v1/providers/{fake_id}")
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_provider_no_changes(client, monkeypatch):
    """Test PATCH /providers/{provider_id} returns 204 on successful update."""
    fake_id = str(uuid.uuid4())
    provider_data = {}

    def fake_update_provider(session, provider_id, new_provider, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.update_provider", fake_update_provider
    )

    resp = client.patch(f"/api/v1/providers/{fake_id}", json=provider_data)
    assert resp.status_code == 204


def test_edit_provider_success(client, monkeypatch):
    """Test PATCH /providers/{provider_id} returns 204 on successful update."""
    fake_id = str(uuid.uuid4())
    provider_data = {"description": DUMMY_DESC}

    def fake_update_provider(session, provider_id, new_provider, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.update_provider", fake_update_provider
    )

    resp = client.patch(f"/api/v1/providers/{fake_id}", json=provider_data)
    assert resp.status_code == 204


def test_edit_provider_not_found(client, monkeypatch):
    """Test PATCH /providers/{provider_id} returns 404 if not found."""
    fake_id = str(uuid.uuid4())
    provider_data = {}

    def fake_update_provider(session, provider_id, new_provider, updated_by):
        raise NoItemToUpdateError("Provider not found")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.update_provider", fake_update_provider
    )

    resp = client.patch(f"/api/v1/providers/{fake_id}", json=provider_data)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Provider not found"


def test_edit_provider_conflict(client, monkeypatch):
    """Test PATCH /providers/{provider_id} returns 409 if conflict error occurs."""
    fake_id = str(uuid.uuid4())
    provider_data = {}

    def fake_update_provider(session, provider_id, new_provider, updated_by):
        raise ConflictError("Provider already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.update_provider", fake_update_provider
    )

    resp = client.patch(f"/api/v1/providers/{fake_id}", json=provider_data)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Provider already exists"


def test_edit_provider_not_null_error(client, monkeypatch):
    """Test PATCH /providers/{provider_id} returns 422 if not null error occurs."""
    fake_id = str(uuid.uuid4())
    provider_data = {}

    def fake_update_provider(session, provider_id, new_provider, updated_by):
        raise NotNullError("Field 'endpoint' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.update_provider", fake_update_provider
    )

    resp = client.patch(f"/api/v1/providers/{fake_id}", json=provider_data)
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


def test_delete_provider_success(client, monkeypatch):
    """Test DELETE /providers/{provider_id} returns 204 on success."""
    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.delete_provider",
        lambda session, provider_id: None,
    )
    resp = client.delete(f"/api/v1/providers/{fake_id}")
    assert resp.status_code == 204


def test_update_provider_state_success(client, monkeypatch):
    """Test PUT /providers/{provider_id}/change_state/{next_state} returns 200."""
    fake_id = str(uuid.uuid4())
    next_state = ProviderStatus.submitted.value

    class FakeProvider:
        id = fake_id
        status = ProviderStatus.draft

    def fake_get_provider(provider_id, session=None):
        return FakeProvider()

    sub_app_v1.dependency_overrides[get_provider] = fake_get_provider

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.change_provider_state", lambda **kwargs: None
    )

    resp = client.put(f"/api/v1/providers/{fake_id}/change_state/{next_state}")
    assert resp.status_code == 200
    sub_app_v1.dependency_overrides = {}


def test_update_provider_state_forbidden(client, monkeypatch):
    """Test PUT /providers/{provider_id}/change_state/{next_state} returns 400."""
    fake_id = str(uuid.uuid4())
    next_state = ProviderStatus.ready.value

    class FakeProvider:
        id = fake_id
        status = ProviderStatus.draft

    def fake_get_provider(provider_id, session=None):
        return FakeProvider()

    sub_app_v1.dependency_overrides[get_provider] = fake_get_provider

    def fake_change_provider_state(**kwargs):
        raise ProviderStateChangeError("forbidden transition")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.change_provider_state",
        fake_change_provider_state,
    )

    resp = client.put(f"/api/v1/providers/{fake_id}/change_state/{next_state}")
    assert resp.status_code == 400
    assert "forbidden transition" in resp.json()["detail"]
    sub_app_v1.dependency_overrides = {}


def test_update_provider_not_existing_state(client, monkeypatch):
    """Test PUT /providers/{provider_id}/change_state/{next_state} returns 422."""
    fake_id = str(uuid.uuid4())
    next_state = 1000  # Invalid state value

    class FakeProvider:
        id = fake_id
        status = ProviderStatus.draft

    def fake_get_provider(provider_id, session=None):
        return FakeProvider()

    sub_app_v1.dependency_overrides[get_provider] = fake_get_provider

    def fake_change_provider_state(**kwargs):
        raise ProviderStateChangeError("forbidden transition")

    monkeypatch.setattr(
        "fed_mgr.v1.providers.endpoints.change_provider_state",
        fake_change_provider_state,
    )

    resp = client.put(f"/api/v1/providers/{fake_id}/change_state/{next_state}")
    assert resp.status_code == 422
    assert "Input should be " in resp.json()["detail"][0]["msg"]
    sub_app_v1.dependency_overrides = {}
