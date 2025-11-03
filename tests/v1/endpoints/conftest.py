"""Fixtures for fed-mgr endpoints tests."""

from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from fed_mgr.auth import check_authentication, check_authorization
from fed_mgr.db import get_session
from fed_mgr.main import app, sub_app_v1
from fed_mgr.v1.models import User
from fed_mgr.v1.users.dependencies import get_current_user


@pytest.fixture
def client():
    """Fixture that returns a FastAPI TestClient for the app.

    Patch authentication dependencies to always allow access for tests
    """
    with TestClient(app, headers={"Authorization": "Bearer fake-token"}) as test_client:
        sub_app_v1.dependency_overrides[check_authentication] = lambda: None
        sub_app_v1.dependency_overrides[check_authorization] = lambda: None
        yield test_client


@pytest.fixture
def session():
    """Create and return a mock session object for testing purposes.

    Returns:
        unittest.mock.Mock: A mock session object.

    """
    session = mock.MagicMock(spec=Session)
    sub_app_v1.dependency_overrides[get_session] = lambda: session
    return session


@pytest.fixture
def current_user():
    """Create and return a mock session object for testing purposes.

    Returns:
        unittest.mock.Mock: A mock session object.

    """
    current_user = mock.MagicMock(spec=User)
    sub_app_v1.dependency_overrides[get_current_user] = lambda: current_user
    return current_user


@pytest.fixture(autouse=True)
def patch_logger(monkeypatch, mock_logger):
    """Patch the logger to use a mock logger during tests."""
    monkeypatch.setattr("fed_mgr.logger.get_logger", lambda *a, **kw: mock_logger)
