"""Fixtures for fed-mgr endpoints tests."""

import uuid
from typing import Any
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from fed_mgr.auth import check_authentication, check_authorization
from fed_mgr.db import get_session
from fed_mgr.main import app, sub_app_v1
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.identity_providers.user_groups.crud import get_user_group
from fed_mgr.v1.identity_providers.user_groups.slas.crud import get_sla
from fed_mgr.v1.models import SLA, IdentityProvider, User, UserGroup
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


@pytest.fixture
def idp_data() -> dict[str, Any]:
    """Return dict with IDP data."""
    return {
        "description": "desc",
        "endpoint": "https://idp.example.com",
        "name": "Test IdP",
        "groups_claim": "groups",
        "protocol": "openid",
        "audience": "aud1",
    }


@pytest.fixture
def idp_dep(idp_data: dict[str, Any]) -> IdentityProvider:
    """Patch get_idp depencency to return a dummy IDP."""
    user_id = uuid.uuid4()
    item = IdentityProvider(
        id=uuid.uuid4(), created_by_id=user_id, updated_by_id=user_id, **idp_data
    )
    sub_app_v1.dependency_overrides[get_idp] = lambda idp_id, session=None: item
    return item


@pytest.fixture
def user_group_data() -> dict[str, Any]:
    """Return dict with User group data."""
    return {"description": "desc", "name": "Test UserGroup"}


@pytest.fixture
def user_group_dep(user_group_data: dict[str, Any]) -> UserGroup:
    """Patch get_idp depencency to return a dummy IDP."""
    user_id = uuid.uuid4()
    item = UserGroup(
        id=uuid.uuid4(),
        created_by_id=user_id,
        updated_by_id=user_id,
        **user_group_data,
    )
    sub_app_v1.dependency_overrides[get_user_group] = lambda idp_id, session=None: item
    return item


@pytest.fixture
def sla_data() -> dict[str, Any]:
    """Return dict with User group data."""
    return {
        "description": "desc",
        "name": "Test UserGroup",
        "url": "http://test.url.it",
        "start_date": "2024-01-01",
        "end_date": "2025-01-01",
    }


@pytest.fixture
def sla_dep(sla_data: dict[str, Any]) -> SLA:
    """Patch get_idp depencency to return a dummy IDP."""
    user_id = uuid.uuid4()
    item = SLA(
        id=uuid.uuid4(),
        created_by_id=user_id,
        updated_by_id=user_id,
        **sla_data,
    )
    sub_app_v1.dependency_overrides[get_sla] = lambda user_group_id, session=None: item
    return item
