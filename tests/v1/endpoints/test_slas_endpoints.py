"""Integration tests for fed_mgr.v1.identity_providers.slas.endpoints.

Tests in this file:
- test_options_slas
- test_create_sla_success
- test_create_sla_conflict
- test_create_sla_not_null_error
- test_create_sla_parent_idp_not_found
- test_get_slas_success
- test_get_sla_success
- test_get_sla_not_found
- test_edit_sla_success
- test_edit_sla_not_found
- test_edit_sla_conflict
- test_edit_sla_not_null_error
- test_delete_sla_success
"""

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel

from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    ItemNotFoundError,
    NotNullError,
)
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.identity_providers.user_groups.crud import get_user_group
from fed_mgr.v1.identity_providers.user_groups.slas.crud import get_sla

DUMMY_DESC = "desc"
DUMMY_NAME = "Test SLA"
DUMMY_URL = "http://test.url.it"
DUMMY_START_DATE = "2024-01-01"
DUMMY_END_DATE = "2025-01-01"
DUMMY_CREATED_AT = datetime.now()


def get_fake_user_group_id() -> str:
    """Patch get_idp depencency to return a dummy IDP."""
    fake_id = str(uuid.uuid4())

    class FakeUserGroup:
        id = fake_id

    sub_app_v1.dependency_overrides[get_user_group] = (
        lambda user_group_id, session=None: FakeUserGroup()
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
def test_options_slas_parent_idp_not_found(client):
    """Test OPTIONS returns 404 if parent_user_group is None."""
    fake_idp_id = str(uuid.uuid4())
    fake_user_group_id = get_fake_user_group_id()

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None

    resp = client.options(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_options_slas_parent_user_group_not_found(client):
    """Test OPTIONS returns 404 if parent_user_group is None."""
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_user_group] = (
        lambda user_group_id, session=None: None
    )

    resp = client.options(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_options_slas(client):
    """Test OPTIONS /idps/{idp_id}/user-groups/ returns 204 and Allow header."""
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()

    resp = client.options(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/"
    )
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


# POST endpoint
def test_create_sla_parent_idp_not_found(client):
    """Test POST returns 404 if parent_user_group is None."""
    fake_idp_id = str(uuid.uuid4())
    fake_user_group_id = str(uuid.uuid4())
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None

    resp = client.post(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/",
        json=sla_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_create_sla_parent_user_group_not_found(client):
    """Test POST returns 404 if parent_user_group is None."""
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = str(uuid.uuid4())
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    sub_app_v1.dependency_overrides[get_user_group] = (
        lambda user_group_id, session=None: None
    )

    resp = client.post(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/",
        json=sla_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_create_sla_success(client, monkeypatch):
    """Test POST creates a user group and returns 201 with id."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    def fake_add_sla(session, sla, created_by, user_group):
        class FakeSLA(SQLModel):
            id: uuid.UUID = fake_id

        return FakeSLA()

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.add_sla",
        fake_add_sla,
    )
    resp = client.post(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/",
        json=sla_data,
    )
    assert resp.status_code == 201
    assert resp.json() == {"id": fake_id}


def test_create_sla_conflict(client, monkeypatch):
    """Test POST returns 409 if user group already exists."""
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    def fake_add_sla(session, sla, created_by, user_group):
        raise ConflictError("SLA", "url", DUMMY_URL)

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.add_sla",
        fake_add_sla,
    )
    resp = client.post(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/",
        json=sla_data,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == f"SLA with url={DUMMY_URL} already exists"


def test_create_sla_not_null_error(client, monkeypatch):
    """Test POST returns 409 if a not null error occurs."""
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    def fake_add_sla(session, sla, created_by, user_group):
        raise NotNullError("SLA", "name")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.add_sla",
        fake_add_sla,
    )

    resp = client.post(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/",
        json=sla_data,
    )
    assert resp.status_code == 422
    assert "can't be NULL" in resp.json()["detail"]


# GET (list) endpoint
def test_get_slas_parent_idp_not_found(client):
    """Test GET returns 404 if parent_user_group is None."""
    fake_idp_id = str(uuid.uuid4())
    fake_user_group_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None

    resp = client.get(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_slas_parent_user_group_not_found(client):
    """Test GET returns 404 if parent_user_group is None."""
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_user_group] = (
        lambda user_group_id, session=None: None
    )

    resp = client.get(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_slas_success(client, monkeypatch):
    """Test GET returns paginated user group list."""
    fake_slas = []
    fake_total = 0
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()

    def fake_get_slas(session, skip, limit, sort, **kwargs):
        return fake_slas, fake_total

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.get_slas",
        fake_get_slas,
    )
    resp = client.get(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/"
    )
    assert resp.status_code == 200
    assert "data" in resp.json()


# GET (by id) endpoint
def test_get_sla_parent_idp_not_found(client):
    """Test GET by id returns 404 if parent_user_group is None."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = str(uuid.uuid4())
    fake_user_group_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None
    sub_app_v1.dependency_overrides[get_sla] = lambda sla_id, session=None: None

    resp = client.get(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_sla_parent_user_group_not_found(client):
    """Test GET by id returns 404 if parent_user_group is None."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_user_group] = (
        lambda user_group_id, session=None: None
    )
    sub_app_v1.dependency_overrides[get_sla] = lambda sla_id, session=None: None

    resp = client.get(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_get_sla_success(client):
    """Test GET by id returns user group."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()

    class FakeSLA(SQLModel):
        id: uuid.UUID = fake_id
        name: str = DUMMY_NAME
        description: str = DUMMY_DESC
        url: str = DUMMY_URL
        start_date: str = DUMMY_START_DATE
        end_date: str = DUMMY_END_DATE
        created_at: datetime = DUMMY_CREATED_AT
        created_by_id: uuid.UUID = fake_id
        updated_at: datetime = DUMMY_CREATED_AT
        updated_by_id: uuid.UUID = fake_id
        user_group: Any = Field(fake_user_group_id, exclude=True)

    def fake_get_sla(user_group_id, session=None):
        return FakeSLA()

    sub_app_v1.dependency_overrides[get_sla] = fake_get_sla

    resp = client.get(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}"
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == fake_id


def test_get_sla_not_found(client):
    """Test GET by id returns 404 if not found."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()

    sub_app_v1.dependency_overrides[get_sla] = lambda sla_id, session=None: None
    resp = client.get(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


# PUT endpoint
def test_edit_sla_parent_idp_not_found(client):
    """Test PUT returns 404 if parent_user_group is None."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = str(uuid.uuid4())
    fake_user_group_id = str(uuid.uuid4())
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}",
        json=sla_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_sla_parent_user_group_not_found(client):
    """Test PUT returns 404 if parent_user_group is None."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = str(uuid.uuid4())
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    sub_app_v1.dependency_overrides[get_user_group] = (
        lambda user_group_id, session=None: None
    )

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}",
        json=sla_data,
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_edit_sla_success(client, monkeypatch):
    """Test PUT returns 204 on success."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    def fake_update_sla(session, sla_id, new_sla, updated_by):
        return None

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.update_sla",
        fake_update_sla,
    )

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}",
        json=sla_data,
    )
    assert resp.status_code == 204


def test_edit_sla_not_found(client, monkeypatch):
    """Test PUT returns 404 if not found."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    def fake_update_sla(session, sla_id, new_sla, updated_by):
        raise ItemNotFoundError("SLA", id=sla_id)

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.update_sla",
        fake_update_sla,
    )

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}",
        json=sla_data,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == f"SLA with ID '{fake_id}' does not exist"


def test_edit_sla_conflict(client, monkeypatch):
    """Test PUT returns 409 if conflict."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    def fake_update_sla(session, sla_id, new_sla, updated_by):
        raise ConflictError("SLA", "url", DUMMY_URL)

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.update_sla",
        fake_update_sla,
    )

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}",
        json=sla_data,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == f"SLA with url={DUMMY_URL} already exists"


def test_edit_sla_not_null_error(client, monkeypatch):
    """Test PUT returns 422 if not null."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()
    sla_data = {
        "name": DUMMY_NAME,
        "description": DUMMY_DESC,
        "url": DUMMY_URL,
        "start_date": DUMMY_START_DATE,
        "end_date": DUMMY_END_DATE,
    }

    def fake_update_sla(session, sla_id, new_sla, updated_by):
        raise NotNullError("SLA", "name")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.update_sla",
        fake_update_sla,
    )

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}",
        json=sla_data,
    )
    assert resp.status_code == 422
    assert "can't be NULL" in resp.json()["detail"]


# DELETE endpoint
def test_delete_sla_parent_idp_not_found(client):
    """Test DELETE returns 404 if parent_user_group is None."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = str(uuid.uuid4())
    fake_user_group_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: None

    resp = client.delete(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_delete_sla_parent_user_group_not_found(client):
    """Test DELETE returns 404 if parent_user_group is None."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = str(uuid.uuid4())

    sub_app_v1.dependency_overrides[get_user_group] = (
        lambda user_group_id, session=None: None
    )

    resp = client.delete(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}"
    )
    assert resp.status_code == 404
    assert "does not exist" in resp.json()["detail"]


def test_delete_sla_success(client, monkeypatch):
    """Test DELETE returns 204 on success."""
    fake_id = str(uuid.uuid4())
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.delete_sla",
        lambda session, sla_id: None,
    )

    resp = client.delete(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}"
    )
    assert resp.status_code == 204


def test_delete_sla_fail(client, monkeypatch):
    """Test DELETE returns 400 on fail."""
    fake_idp_id = get_fake_idp_id()
    fake_user_group_id = get_fake_user_group_id()
    fake_id = str(uuid.uuid4())

    def fake_delete_sla(session, sla_id):
        raise DeleteFailedError("Failed to delete item")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.delete_sla",
        fake_delete_sla,
    )

    resp = client.delete(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}"
    )
    assert resp.status_code == 400
