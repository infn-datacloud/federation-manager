"""Fixtures for fed-mgr tests."""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from fed_mgr.auth import check_authentication, check_authorization
from fed_mgr.main import app, sub_app_v1


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
    return mock.Mock()


@pytest.fixture
def mock_logger():
    """Fixture that returns a mock logger object for testing purposes."""
    logger = mock.Mock()
    return logger
