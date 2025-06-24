"""Unit tests to create_fake_user and delete_fake_user."""

import uuid
from unittest import mock

from fed_mgr.v1.users.crud import create_fake_user, delete_fake_user


def test_create_fake_user_creates_new(monkeypatch):
    """Test create_fake_user creates a new user if not present."""
    session = mock.Mock()
    monkeypatch.setattr(
        "fed_mgr.v1.users.crud.get_users", lambda session, **kwargs: ([], 0)
    )
    monkeypatch.setattr("fed_mgr.v1.users.crud.add_user", lambda session, user: None)
    result = create_fake_user(session)
    assert result is None


def test_create_fake_user_returns_existing(monkeypatch):
    """Test create_fake_user returns None if user already exists (no-op)."""
    session = mock.Mock()
    fake_user = mock.Mock()
    monkeypatch.setattr(
        "fed_mgr.v1.users.crud.get_users", lambda session, **kwargs: ([fake_user], 1)
    )
    result = create_fake_user(session)
    assert result is None


def test_delete_fake_user(monkeypatch):
    """Test delete_fake_user calls delete_user with correct arguments if user exists."""
    session = mock.Mock()
    fake_id = uuid.uuid4()
    called = {}

    def fake_get_users(session, **kwargs):
        return [mock.Mock(id=fake_id)], 1

    def fake_delete_user(session, user_id):
        called["session"] = session
        called["user_id"] = user_id

    monkeypatch.setattr("fed_mgr.v1.users.crud.get_users", fake_get_users)
    monkeypatch.setattr("fed_mgr.v1.users.crud.delete_user", fake_delete_user)
    delete_fake_user(session)
    assert called["session"] is session
    assert called["user_id"] == fake_id
