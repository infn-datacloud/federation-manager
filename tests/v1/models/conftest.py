"""Test fixtures for v1 models.

This module provides pytest fixtures that create and persist SQLModel-based
models used across model tests. Fixtures use an in-memory SQLite database and
are designed to be lightweight and reusable.

Available fixtures:
    - engine: session-scoped in-memory SQLite engine with foreign keys enabled
    - db_session: a transactional session rolled back after each test
    - user_model: a persisted User instance
    - idp_model: a persisted IdentityProvider linked to `user_model`
    - user_group_model: a persisted UserGroup linked to `idp_model`
    - sla_model: a persisted SLA linked to `user_group_model`
    - provider_model: a persisted Provider linked to `user_model`
    - region_model: a persisted Region linked to `provider_model`
    - project_model: a persisted Project linked to `provider_model`

These fixtures add objects to the test session database but do not commit so
tests can control transaction boundaries via the `db_session` fixture.
"""

from datetime import date

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, StaticPool, create_engine, text

from fed_mgr.v1.models import (
    SLA,
    IdentityProvider,
    Project,
    Provider,
    Region,
    User,
    UserGroup,
)
from tests.utils import random_lower_string


@pytest.fixture(scope="session")
def engine():
    """Create an in-memory SQLite engine for the whole test session.

    StaticPool ensures the same connection is reused.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with engine.connect() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine: Engine):
    """Create a new database session for a test and rolls back after."""
    connection = engine.connect()
    transaction = connection.begin()

    session = sessionmaker(bind=connection)()

    yield session  # This is where the test runs

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def user_model(db_session: Session) -> User:
    """Create and add a sample User to the current test session.

    The created user is added to `db_session` but not committed so the test
    can control transaction lifecycle.
    """
    sub = "user-123"
    name = "John Doe"
    email = "john.doe@example.com"
    issuer = "https://issuer.example.com"
    user = User(sub=sub, name=name, email=email, issuer=issuer)
    db_session.add(user)
    return user


@pytest.fixture
def idp_model(db_session: Session, user_model: User) -> IdentityProvider:
    """Create and add a sample IdentityProvider linked to `user_model`.

    The instance is added to `db_session` and can be used by other fixtures or
    tests that require an identity provider.
    """
    endpoint = "https://example.com"
    name = "Test IdP"
    groups_claim = "groups"
    protocol = "openid"
    audience = "aud1"
    desc = "A test identity provider."
    idp = IdentityProvider(
        created_by=user_model,
        updated_by=user_model,
        description=desc,
        endpoint=endpoint,
        name=name,
        groups_claim=groups_claim,
        protocol=protocol,
        audience=audience,
    )
    db_session.add(idp)
    return idp


@pytest.fixture
def user_group_model(
    db_session: Session, user_model: User, idp_model: IdentityProvider
) -> UserGroup:
    """Create and add a sample UserGroup linked to `idp_model`.

    Useful for tests that exercise group-related logic and relationships.
    """
    desc = "desc"
    name = "Test Group"
    group = UserGroup(
        created_by=user_model,
        updated_by=user_model,
        name=name,
        description=desc,
        idp=idp_model,
    )
    db_session.add(group)
    return group


@pytest.fixture
def sla_model(
    db_session: Session, user_model: User, user_group_model: UserGroup
) -> SLA:
    """Create and add a sample SLA linked to `user_group_model`.

    Populates typical SLA fields (name, url, dates) useful for model tests.
    """
    name = "Test SLA"
    desc = "desc"
    url = "https://example.com"
    start_date = date(2024, 1, 1)
    end_date = date(2025, 1, 1)
    sla = SLA(
        created_by=user_model,
        updated_by=user_model,
        name=name,
        description=desc,
        url=url,
        start_date=start_date,
        end_date=end_date,
        user_group=user_group_model,
    )
    db_session.add(sla)
    return sla


@pytest.fixture
def provider_model(db_session: Session, user_model: User) -> Provider:
    """Create and add a sample Provider linked to `user_model`.

    The provider includes minimal authentication and admin details for tests.
    """
    name = "foo"
    desc = "desc"
    provider_type = "openstack"
    auth_endpoint = "https://example.com/auth"
    is_pub = True
    emails = ["admin@example.com"]
    provider = Provider(
        created_by=user_model,
        updated_by=user_model,
        name=name,
        description=desc,
        type=provider_type,
        auth_endpoint=auth_endpoint,
        is_public=is_pub,
        support_emails=emails,
        rally_username=random_lower_string(),
        rally_password=random_lower_string(),
        site_admins=[user_model],
    )
    db_session.add(provider)
    return provider


@pytest.fixture
def region_model(
    db_session: Session, user_model: User, provider_model: Provider
) -> Region:
    """Create and add a sample Region linked to `provider_model`.

    Useful for tests that require provider/region relationships.
    """
    name = "eu-west-1"
    desc = "EU West 1"
    region = Region(
        created_by=user_model,
        updated_by=user_model,
        name=name,
        description=desc,
        provider=provider_model,
    )
    db_session.add(region)
    return region


@pytest.fixture
def project_model(
    db_session: Session, user_model: User, provider_model: Provider
) -> Project:
    """Create and add a sample Project linked to `provider_model`.

    The fixture populates a sample iaas_project_id and basic descriptive fields.
    """
    name = "project"
    desc = "example desc"
    iaas_id = "12345"
    project = Project(
        created_by=user_model,
        updated_by=user_model,
        name=name,
        description=desc,
        iaas_project_id=iaas_id,
        provider=provider_model,
    )
    db_session.add(project)
    return project
