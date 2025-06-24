"""Fixtures for fed-mgr endpoints tests."""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from fed_mgr.auth import check_authentication, check_authorization
from fed_mgr.main import app, sub_app_v1
from fed_mgr.v1.users.dependencies import get_current_user
from fed_mgr.v1.users.schemas import User


@pytest.fixture
def client():
    """Fixture that returns a FastAPI TestClient for the app.

    Patch authentication dependencies to always allow access for tests
    """
    with TestClient(app, headers={"Authorization": "Bearer fake-token"}) as test_client:
        sub_app_v1.dependency_overrides[check_authentication] = lambda: None
        sub_app_v1.dependency_overrides[check_authorization] = lambda: None
        sub_app_v1.dependency_overrides[get_current_user] = lambda: mock.MagicMock(
            spec=User
        )
        yield test_client


@pytest.fixture(autouse=True)
def patch_logger(monkeypatch, mock_logger):
    """Patch the logger to use a mock logger during tests."""
    monkeypatch.setattr("fed_mgr.logger.get_logger", lambda *a, **kw: mock_logger)
