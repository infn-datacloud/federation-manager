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

from fed_mgr.exceptions import ConflictError, NoItemToUpdateError, NotNullError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.identity_providers.user_groups.crud import get_user_group
from fed_mgr.v1.identity_providers.user_groups.slas.crud import get_sla

DUMMY_DESC = "desc"
DUMMY_NAME = "Test SLA"
DUMMY_URL = "http://test.url.it"
DUMMY_START_DATE = "2024-01-01"
DUMMY_END_DATE = "2025-01-01"
DUMMY_CREATED_AT = "2024-01-01T00:00:00Z"


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

    class FakeSLA:
        id = fake_id

    def fake_add_sla(session, sla, created_by, parent_user_group):
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

    def fake_add_sla(session, sla, created_by, parent_user_group):
        raise ConflictError("User group already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.add_sla",
        fake_add_sla,
    )
    resp = client.post(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/",
        json=sla_data,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "User group already exists"


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

    def fake_add_sla(session, sla, created_by, parent_user_group):
        raise NotNullError("Field 'name' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.add_sla",
        fake_add_sla,
    )

    resp = client.post(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/",
        json=sla_data,
    )
    assert resp.status_code == 409
    assert "cannot be null" in resp.json()["detail"]


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

    class FakeSLA:
        id = fake_id
        name = DUMMY_NAME
        description = DUMMY_DESC
        url = DUMMY_URL
        start_date = DUMMY_START_DATE
        end_date = DUMMY_END_DATE
        user_group = fake_user_group_id
        created_at = DUMMY_CREATED_AT
        created_by = fake_id
        updated_at = DUMMY_CREATED_AT
        updated_by = fake_id

        def model_dump(self):
            return {
                "id": self.id,
                "description": self.description,
                "name": self.name,
                "url": self.url,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "user_group": self.user_group,
                "created_at": self.created_at,
                "created_by": self.created_by,
                "updated_at": self.updated_at,
                "updated_by": self.updated_by,
            }

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
        raise NoItemToUpdateError("User group not found")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.update_sla",
        fake_update_sla,
    )

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}",
        json=sla_data,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User group not found"


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
        raise ConflictError("User group already exists")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.update_sla",
        fake_update_sla,
    )

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}",
        json=sla_data,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "User group already exists"


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
        raise NotNullError("Field 'name' cannot be null")

    monkeypatch.setattr(
        "fed_mgr.v1.identity_providers.user_groups.slas.endpoints.update_sla",
        fake_update_sla,
    )

    resp = client.put(
        f"/api/v1/idps/{fake_idp_id}/user-groups/{fake_user_group_id}/slas/{fake_id}",
        json=sla_data,
    )
    assert resp.status_code == 422
    assert "cannot be null" in resp.json()["detail"]


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
