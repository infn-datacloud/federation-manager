"""Integration tests for fed_mgr.v1.users.endpoints using FastAPI TestClient."""

import uuid

import pytest

from fed_mgr.auth import check_authentication
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.users.crud import get_user


@pytest.fixture(autouse=True)
def patch_logger(monkeypatch, mock_logger):
    """Patch the logger to use a mock logger during tests."""
    monkeypatch.setattr("fed_mgr.logger.get_logger", lambda *a, **kw: mock_logger)


def test_options_users(client):
    """Test OPTIONS /users/ returns 204 and Allow header."""
    resp = client.options("/api/v1/users/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_user_success(client, monkeypatch):
    """Test POST /users/ creates user and returns 201 with user id."""
    user_data = {
        "sub": "testsub",
        "name": "Test User",
        "email": "test@example.com",
        "issuer": "https://issuer.example.com",
    }
    fake_id = str(uuid.uuid4())

    class FakeUser:
        id = fake_id

    def fake_add_user(session, user):
        return FakeUser()

    monkeypatch.setattr("fed_mgr.v1.users.endpoints.add_user", fake_add_user)
    resp = client.post("/api/v1/users/", json=user_data)
    assert resp.status_code == 201
    assert resp.json() == {"id": fake_id}


def test_create_user_no_body(client, monkeypatch):
    """Test POST /users/ with no body uses AuthenticationDep and returns 201."""
    fake_id = str(uuid.uuid4())

    class FakeAuth:
        subject = "testsub"
        issuer = "https://issuer.example.com"

        def __init__(self):
            self.user_info = {"name": "Test User", "email": "test@example.com"}

    def retrieve_info_from_fake_token(authz_creds=None):
        return FakeAuth()

    class FakeUser:
        id = fake_id

    def fake_add_user(session, user):
        return FakeUser()

    # Patch AuthenticationDep to return our fake auth info
    sub_app_v1.dependency_overrides[check_authentication] = (
        retrieve_info_from_fake_token
    )

    monkeypatch.setattr("fed_mgr.v1.users.endpoints.add_user", fake_add_user)

    resp = client.post("/api/v1/users/")
    assert resp.status_code == 201
    assert resp.json() == {"id": fake_id}


def test_create_user_conflict(client, monkeypatch):
    """Test POST /users/ returns 409 if user already exists."""
    from fed_mgr.exceptions import ConflictError

    user_data = {
        "sub": "testsub",
        "name": "Test User",
        "email": "test@example.com",
        "issuer": "https://issuer.example.com",
    }

    def fake_add_user(session, user):
        raise ConflictError("User already exists")

    monkeypatch.setattr("fed_mgr.v1.users.endpoints.add_user", fake_add_user)
    resp = client.post("/api/v1/users/", json=user_data)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "User already exists"


def test_get_users_success(client, monkeypatch):
    """Test GET /users/ returns paginated user list."""
    fake_users = []
    fake_total = 0

    def fake_get_users(session, skip, limit, sort, **kwargs):
        return fake_users, fake_total

    monkeypatch.setattr("fed_mgr.v1.users.endpoints.get_users", fake_get_users)
    resp = client.get("/api/v1/users/")
    assert resp.status_code == 200
    assert "data" in resp.json()


def test_get_user_success(client, monkeypatch):
    """Test GET /users/{user_id} returns user if found."""
    fake_id = str(uuid.uuid4())

    class FakeUser:
        id = fake_id
        sub = "testsub"
        name = "Test User"
        email = "test@example.com"
        issuer = "https://issuer.example.com"
        created_at = "2024-01-01T00:00:00Z"

    def fake_get_user(user_id, session=None):
        return FakeUser()

    sub_app_v1.dependency_overrides[get_user] = fake_get_user

    resp = client.get(f"/api/v1/users/{fake_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == fake_id


def test_get_user_not_found(client, monkeypatch):
    """Test GET /users/{user_id} returns 404 if user not found."""
    fake_id = str(uuid.uuid4())

    def fake_get_user(user_id, session=None):
        return None

    sub_app_v1.dependency_overrides[get_user] = fake_get_user

    resp = client.get(f"/api/v1/users/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == f"User with ID '{fake_id}' does not exist"


def test_delete_user_success(client, monkeypatch):
    """Test DELETE /users/{user_id} returns 204 on success."""
    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "fed_mgr.v1.users.crud.delete_user", lambda session, user_id: None
    )
    resp = client.delete(f"/api/v1/users/{fake_id}")
    assert resp.status_code == 204
