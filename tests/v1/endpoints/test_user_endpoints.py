"""Integration tests for fed_mgr.v1.users.endpoints using FastAPI TestClient."""

import uuid
from unittest.mock import patch

from fed_mgr.auth import check_authentication
from fed_mgr.exceptions import ConflictError, DeleteFailedError
from fed_mgr.main import sub_app_v1
from fed_mgr.v1.models import User
from fed_mgr.v1.schemas import ItemID
from fed_mgr.v1.users.crud import get_user
from fed_mgr.v1.users.dependencies import get_current_user
from fed_mgr.v1.users.schemas import UserCreate


def test_options_users(client):
    """Test OPTIONS /users/ returns 204 and Allow header."""
    resp = client.options("/api/v1/users/")
    assert resp.status_code == 204
    assert "allow" in resp.headers or "Allow" in resp.headers


def test_create_user(client, session, user_data):
    """Test POST /users/ with no body uses AuthenticationDep and returns 201."""
    fake_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[check_authentication] = lambda: user_data
    with patch(
        "fed_mgr.v1.users.endpoints.add_user", return_value=ItemID(id=fake_id)
    ) as mock_create:
        resp = client.post("/api/v1/users/")
        assert resp.status_code == 201
        assert resp.json() == {"id": str(fake_id)}
        mock_create.assert_called_once_with(
            session=session, user=UserCreate(**user_data)
        )


def test_create_user_conflict(client, session, user_data):
    """Test POST /users/ returns 409 if user already exists."""
    err_msg = "Error message"
    sub_app_v1.dependency_overrides[check_authentication] = lambda: user_data
    with patch(
        "fed_mgr.v1.users.endpoints.add_user", side_effect=ConflictError(err_msg)
    ) as mock_create:
        resp = client.post("/api/v1/users/")
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg
        mock_create.assert_called_once_with(
            session=session, user=UserCreate(**user_data)
        )


def test_get_users_success(client, session, user_data):
    """Test GET /users/ returns paginated user list."""
    with patch(
        "fed_mgr.v1.users.endpoints.get_users", return_value=([], 0)
    ) as mock_get:
        resp = client.get("/api/v1/users/")
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 0
        assert "page" in resp.json()
        assert "links" in resp.json()
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at"
        )

    fake_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user1 = User(**user_data, id=fake_id, created_by_id=user_id, updated_by_id=user_id)
    with patch(
        "fed_mgr.v1.users.endpoints.get_users", return_value=([user1], 1)
    ) as mock_get:
        resp = client.get("/api/v1/users/")
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 1
        assert "page" in resp.json()
        assert "links" in resp.json()
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at"
        )

    user2 = User(**user_data, id=fake_id, created_by_id=user_id, updated_by_id=user_id)
    with patch(
        "fed_mgr.v1.users.endpoints.get_users", return_value=([user1, user2], 2)
    ) as mock_get:
        resp = client.get("/api/v1/users/")
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "data" in resp.json()
        assert len(resp.json()["data"]) == 2
        assert "page" in resp.json()
        assert "links" in resp.json()
        mock_get.assert_called_once_with(
            session=session, skip=0, limit=5, sort="-created_at"
        )


def test_get_user_success(client, user_dep, user_data):
    """Test GET /users/{user_id} returns user if found."""
    sub_app_v1.dependency_overrides[check_authentication] = lambda: user_data
    resp = client.get(f"/api/v1/users/{user_dep.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(user_dep.id)


def test_get_me(client, user_dep):
    """Test GET /users/{user_id} returns user if found."""
    sub_app_v1.dependency_overrides[get_current_user] = lambda: user_dep
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(user_dep.id)


def test_get_user_not_found(client, user_data):
    """Test GET /users/{user_id} returns 404 if user not found."""
    fake_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[check_authentication] = lambda: user_data
    sub_app_v1.dependency_overrides[get_user] = lambda: None

    resp = client.get(f"/api/v1/users/{fake_id}")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
    assert resp.json()["detail"] == f"User with ID '{fake_id}' does not exist"


def test_delete_user_success(client, session, user_data):
    """Test DELETE /users/{user_id} returns 204 on success."""
    fake_id = uuid.uuid4()
    sub_app_v1.dependency_overrides[check_authentication] = lambda: user_data

    with patch(
        "fed_mgr.v1.users.endpoints.delete_user", return_value=None
    ) as mock_delete:
        resp = client.delete(f"/api/v1/users/{fake_id}")
        assert resp.status_code == 204
        mock_delete.assert_called_once_with(session=session, user_id=fake_id)


def test_delete_user_fail(client, session, user_data):
    """Test DELETE /users/{user_id} returns 400 on fail."""
    fake_id = uuid.uuid4()
    err_msg = "Error message"
    sub_app_v1.dependency_overrides[check_authentication] = lambda: user_data

    with patch(
        "fed_mgr.v1.users.endpoints.delete_user", side_effect=DeleteFailedError(err_msg)
    ) as mock_delete:
        resp = client.delete(f"/api/v1/users/{fake_id}")
        assert resp.status_code == 409
        assert resp.json()["status"] == 409
        assert resp.json()["detail"] == err_msg
        mock_delete.assert_called_once_with(session=session, user_id=fake_id)


def test_delete_me(client, user_dep):
    """Delete me."""
    sub_app_v1.dependency_overrides[get_current_user] = lambda: user_dep
    resp = client.delete(f"/api/v1/users/{user_dep.id}")
    assert resp.status_code == 403
    assert resp.json()["status"] == 403
    assert resp.json()["detail"] == "User can't delete themselves"
