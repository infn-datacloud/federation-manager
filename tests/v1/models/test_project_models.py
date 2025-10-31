"""Unit tests for the Project model and related schemas.

This module verifies the SQLModel-backed `Project` model and its behaviour in
the database. Tests focus on:

- Basic model fields and types
- Unique constraints and integrity behavior for project/provider combinations
- Root project relationship behavior for a Provider
- Relationship containers and audit mixins

Fixtures used:
    - db_session: transactional SQLModel session scoped to a test
    - user_model: a sample persisted User used as creator/updater
    - provider_model: a sample Provider instance
    - project_model: a persisted Project used as an existing fixture
"""

import uuid
from datetime import datetime

import pytest
import sqlalchemy.exc
from sqlmodel import Session

from fed_mgr.v1.models import Project, Provider, User
from fed_mgr.v1.providers.projects.schemas import ProjectBase
from fed_mgr.v1.schemas import CreationTime, ItemID, UpdateTime
from tests.utils import random_lower_string


def test_project_model(
    db_session: Session, user_model: User, provider_model: Provider
) -> None:
    """Verify Project fields, relationships and audit mixins.

    Creates a `Project` attached to `provider_model`, commits it and asserts that
    required mixins (ID, creation/update timestamps) are present, typed fields are
    coerced correctly, and relationships (provider, sla, regions) are in expected
    initial states.
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
    db_session.commit()

    assert isinstance(project, ItemID)
    assert isinstance(project, CreationTime)
    assert isinstance(project, UpdateTime)
    assert isinstance(project, ProjectBase)
    assert isinstance(project.id, uuid.UUID)
    assert isinstance(project.created_at, datetime)
    assert isinstance(project.updated_at, datetime)
    assert project.created_by == user_model
    assert project.created_by_id == user_model.id
    assert project.updated_by == user_model
    assert project.updated_by_id == user_model.id
    assert project.name == name
    assert project.description == desc
    assert project.iaas_project_id == iaas_id
    assert project.provider == provider_model
    assert project.provider_id == provider_model.id
    assert project.sla is None
    assert project.sla_id is None
    assert project.regions == []

    assert user_model.created_projects == [project]
    assert user_model.updated_projects == [project]


def test_duplicate_project(
    db_session: Session,
    user_model: User,
    provider_model: Provider,
    project_model: Project,
) -> None:
    """Ensure uniqueness constraint on (iaas_project_id, provider_id).

    Attempting to create a project with the same `iaas_project_id` under the
    same provider should raise an IntegrityError due to the unique constraint.
    """
    project = Project(
        created_by=user_model,
        updated_by=user_model,
        name="Project X",
        iaas_project_id=project_model.iaas_project_id,
        provider=provider_model,
    )
    db_session.add(project)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match="UNIQUE constraint failed: project.iaas_project_id, project.provider_id",
    ):
        db_session.commit()


def test_same_project_different_provider(
    db_session: Session, user_model: User, project_model: Project
) -> None:
    """Allow same iaas_project_id under a different provider.

    Creating a project with the same `iaas_project_id` but under a different
    provider should succeed and result in a distinct Project record.
    """
    provider = Provider(
        created_by=user_model,
        updated_by=user_model,
        name="Another Provider",
        type="openstack",
        auth_endpoint="https://another.endpoint.com",
        support_emails=["fake@email.com"],
        rally_username=random_lower_string(),
        rally_password=random_lower_string(),
        site_admins=[user_model],
    )
    project = Project(
        created_by=user_model,
        updated_by=user_model,
        name=project_model.name,
        iaas_project_id=project_model.iaas_project_id,
        provider=provider,
    )
    db_session.add(project)
    db_session.commit()

    assert project.id is not None
    assert project.id != project_model.id


def test_is_root_project(
    db_session: Session, user_model: User, project_model: Project
) -> None:
    """Verify assignment of a root project to a provider.

    Creating a project with `is_root=True` for a provider should mark that
    project as the provider's `root_project`.
    """
    provider = project_model.provider
    assert provider.root_project is None

    root_project = Project(
        created_by=user_model,
        updated_by=user_model,
        name="Root project",
        iaas_project_id="09876",
        is_root=True,
        provider=provider,
    )
    db_session.add(root_project)
    db_session.commit()

    assert provider.root_project == root_project


def test_only_one_root_project(
    db_session: Session, user_model: User, project_model: Project
) -> None:
    """Ensure only one root project exists per provider.

    Marking an existing project as root should set it as the provider's
    `root_project`. Creating another project with `is_root=True` for the same
    provider should violate the unique constraint and raise an IntegrityError
    (SQLite behavior verified here).
    """
    # SQLite
    provider = project_model.provider
    assert provider.root_project is None

    project_model.is_root = True
    db_session.add(project_model)
    assert provider.root_project == project_model

    root_project = Project(
        created_by=user_model,
        updated_by=user_model,
        name="Root project",
        iaas_project_id="09876",
        is_root=True,
        provider=provider,
    )
    db_session.add(root_project)

    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match="UNIQUE constraint failed: project.provider_id",
    ):
        db_session.commit()

    # TODO: test with MySQL
