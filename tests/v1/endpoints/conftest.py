"""Fixtures for fed-mgr endpoints tests."""

import os
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
from fed_mgr.v1.models import (
    SLA,
    IdentityProvider,
    IdpOverrides,
    Project,
    Provider,
    Region,
    RegionOverrides,
    User,
    UserGroup,
)
from fed_mgr.v1.providers.crud import get_provider
from fed_mgr.v1.providers.identity_providers.crud import get_idp_overrides
from fed_mgr.v1.providers.projects.crud import get_project
from fed_mgr.v1.providers.projects.regions.crud import get_region_overrides
from fed_mgr.v1.providers.regions.crud import get_region
from fed_mgr.v1.users.crud import get_user
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
    sub_app_v1.dependency_overrides[get_idp] = lambda: item
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
    sub_app_v1.dependency_overrides[get_user_group] = lambda: item
    return item


@pytest.fixture
def sla_data() -> dict[str, Any]:
    """Return dict with User group data."""
    return {
        "description": "desc",
        "name": "Test UserGroup",
        "url": "https://test.url.it",
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
    sub_app_v1.dependency_overrides[get_sla] = lambda: item
    return item


@pytest.fixture
def user_data() -> dict[str, Any]:
    """Return dict with User data."""
    return {
        "sub": "Testsub",
        "name": "Test User",
        "email": "test@example.com",
        "iss": "https://issuer.example.com",  # Used in Flaat UserInfos
        "issuer": "https://issuer.example.com",  # Alias of 'iss' used in UserCreate
    }


@pytest.fixture
def user_dep(user_data: dict[str, Any]) -> User:
    """Patch get_idp depencency to return a dummy IDP."""
    item = User(id=uuid.uuid4(), **user_data)
    sub_app_v1.dependency_overrides[get_user] = lambda: item
    return item


@pytest.fixture
def provider_data() -> dict[str, Any]:
    """Return dict with User group data."""
    return {
        "description": "desc",
        "name": "Test Provider",
        "type": "openstack",
        "auth_endpoint": "https://example.com/auth",
        "support_emails": ["admin@example.com"],
        "rally_username": os.getenv("user", "user"),
        "rally_password": os.getenv("password", "password"),
    }


@pytest.fixture
def provider_dep(provider_data: dict[str, Any]) -> Provider:
    """Patch get_idp depencency to return a dummy IDP."""
    user_id = uuid.uuid4()
    item = Provider(
        id=uuid.uuid4(), created_by_id=user_id, updated_by_id=user_id, **provider_data
    )
    sub_app_v1.dependency_overrides[get_provider] = lambda: item
    return item


@pytest.fixture
def region_data() -> dict[str, Any]:
    """Return dict with User group data."""
    return {"description": "desc", "name": "Test Region"}


@pytest.fixture
def region_dep(region_data: dict[str, Any]) -> Region:
    """Patch get_idp depencency to return a dummy IDP."""
    user_id = uuid.uuid4()
    item = Region(
        id=uuid.uuid4(), created_by_id=user_id, updated_by_id=user_id, **region_data
    )
    sub_app_v1.dependency_overrides[get_region] = lambda: item
    return item


@pytest.fixture
def project_data() -> dict[str, Any]:
    """Return dict with User group data."""
    return {"description": "desc", "name": "Test Project", "iaas_project_id": "12345"}


@pytest.fixture
def project_dep(project_data: dict[str, Any]) -> Project:
    """Patch get_idp depencency to return a dummy IDP."""
    user_id = uuid.uuid4()
    item = Project(
        id=uuid.uuid4(), created_by_id=user_id, updated_by_id=user_id, **project_data
    )
    sub_app_v1.dependency_overrides[get_project] = lambda: item
    return item


@pytest.fixture
def idp_overrides_data() -> dict[str, Any]:
    """Return dict with User group data."""
    return {
        "name": "Test IdP",
        "groups_claim": "groups",
        "protocol": "openid",
        "audience": "aud1",
    }


@pytest.fixture
def idp_overrides_dep(idp_overrides_data: dict[str, Any]) -> IdpOverrides:
    """Patch get_idp depencency to return a dummy IDP."""
    user_id = uuid.uuid4()
    item = IdpOverrides(
        idp_id=uuid.uuid4(),
        created_by_id=user_id,
        updated_by_id=user_id,
        **idp_overrides_data,
    )
    sub_app_v1.dependency_overrides[get_idp_overrides] = lambda: item
    return item


@pytest.fixture
def reg_overrides_data() -> dict[str, Any]:
    """Return dict with User group data."""
    return {
        "default_public_net": "pub-net",
        "default_private_net": "priv-net",
        "private_net_proxy_host": "host",
        "private_net_proxy_user": "user",
    }


@pytest.fixture
def reg_overrides_dep(reg_overrides_data: dict[str, Any]) -> RegionOverrides:
    """Patch get_reg depencency to return a dummy IDP."""
    user_id = uuid.uuid4()
    item = RegionOverrides(
        region_id=uuid.uuid4(),
        created_by_id=user_id,
        updated_by_id=user_id,
        **reg_overrides_data,
    )
    sub_app_v1.dependency_overrides[get_region_overrides] = lambda: item
    return item
