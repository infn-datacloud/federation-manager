"""Unit tests for `fed_mgr.v1.providers.regions` schemas and models.

This module verifies the `Region` SQLModel-backed model and related
schema behaviour used by the providers/regions package. The tests cover:

- Basic model mixins and typed fields (ID, creation/update timestamps).
- Database constraints (unique region per provider).
- Relationship wiring to `Provider` and the owning `User`.
- Default containers (linked_projects) and identity of root projects.

Fixtures used:
    - db_session: transactional SQLModel session scoped to a test.
    - user_model: persisted `User` used as creator/updater.
    - provider_model / region_model: convenience persisted models used by
        tests that require pre-existing providers/regions.
"""

import uuid
from datetime import datetime

import pytest
import sqlalchemy.exc
from sqlmodel import Session

from fed_mgr.v1.models import Project, Provider, Region, RegionOverrides, User
from fed_mgr.v1.providers.regions.schemas import RegionBase
from fed_mgr.v1.schemas import CreationTime, ItemID, UpdateTime
from tests.utils import random_lower_string


def test_region_model(
    db_session: Session, user_model: User, provider_model: Provider
) -> None:
    """Verify Region model fields, types and relationships.

    The test creates a `Region` instance attached to `provider_model`,
    persists it and asserts that mixins and relationship attributes are set
    as expected.
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
    db_session.commit()

    assert isinstance(region, ItemID)
    assert isinstance(region, CreationTime)
    assert isinstance(region, UpdateTime)
    assert isinstance(region, RegionBase)
    assert isinstance(region.id, uuid.UUID)
    assert isinstance(region.created_at, datetime)
    assert isinstance(region.updated_at, datetime)
    assert region.created_by == user_model
    assert region.created_by_id == user_model.id
    assert region.updated_by == user_model
    assert region.updated_by_id == user_model.id
    assert region.name == name
    assert region.description == desc
    assert region.provider == provider_model
    assert region.provider_id == provider_model.id
    assert region.linked_projects == []

    assert user_model.created_regions == [region]
    assert user_model.updated_regions == [region]


def test_duplicate_region(
    db_session: Session,
    user_model: User,
    provider_model: Provider,
    region_model: Region,
) -> None:
    """Ensure the DB enforces unique region names per provider.

    Creating a second Region with the same name under the same provider
    should raise an IntegrityError on commit due to the unique constraint.
    """
    user = Region(
        created_by=user_model,
        updated_by=user_model,
        name=region_model.name,
        provider=provider_model,
    )
    db_session.add(user)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match="UNIQUE constraint failed: region.name, region.provider_id",
    ):
        db_session.commit()


def test_same_region_different_provider(
    db_session: Session, user_model: User, region_model: Region
) -> None:
    """Verify the same region name can exist under a different provider.

    This test creates a new provider (with non-sensitive test credentials)
    and ensures creating a Region with the same name succeeds because the
    uniqueness is scoped to the provider.
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

    region = Region(
        created_by=user_model,
        updated_by=user_model,
        name=region_model.name,
        provider=provider,
    )

    db_session.add(region)
    db_session.commit()

    assert region.id is not None
    assert region.id != region_model.id


def test_delete_reg_overrides_on_cascade(
    db_session: Session, user_model: User, region_model: Region, project_model: Project
) -> None:
    """Can't exist idp with same endpoint."""
    region_overrides = RegionOverrides(created_by=user_model, updated_by=user_model)
    project_model.regions.append(region_overrides)
    region_model.linked_projects.append(region_overrides)
    db_session.add(project_model)
    db_session.commit()

    db_session.delete(project_model)
    assert region_model.linked_projects == []
    db_session.commit()
