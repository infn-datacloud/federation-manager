"""Unit tests for region/project configuration overrides (RegionOverrides).

This module contains unit tests that verify the SQLModel-backed
`RegionOverrides` model used to capture project-specific configuration for a
given region. Tests validate:

- Timestamp mixins and audit fields (created_by/updated_by)
- Network override fields (public/private network defaults and proxy
    settings)
- Relationship linkage to `Project` and `Region` models

Fixtures used:
    - db_session: transactional SQLModel session scoped to a test
    - user_model: sample persisted User used as creator/updater
    - project_model: sample Project instance
    - region_model: sample Region instance
"""

from datetime import datetime

import pytest
import sqlalchemy.exc
from sqlmodel import Session

from fed_mgr.v1.models import Project, Region, RegionOverrides, User
from fed_mgr.v1.schemas import CreationTime, UpdateTime


def test_region_overrides_model(
    db_session: Session, user_model: User, region_model: Region, project_model: Project
):
    """Verify RegionOverrides fields, relationships and audit mixins.

    The fixture creates a `RegionOverrides` instance linking a project and a
    region, sets several network-related override fields, persists the object,
    and asserts that values and relationships are stored and exposed as
    expected.
    """
    pub_net = "pub-net"
    priv_net = "priv-net"
    proxy_host = "192.168.1.1:1234"
    proxy_user = "my-user"
    data = RegionOverrides(
        created_by=user_model,
        updated_by=user_model,
        default_public_net=pub_net,
        default_private_net=priv_net,
        private_net_proxy_host=proxy_host,
        private_net_proxy_user=proxy_user,
        project=project_model,
        region=region_model,
    )
    db_session.add(data)
    db_session.commit()

    assert isinstance(data, CreationTime)
    assert isinstance(data, UpdateTime)
    assert isinstance(data.created_at, datetime)
    assert data.created_by == user_model
    assert data.created_by_id == user_model.id
    assert data.updated_by == user_model
    assert data.updated_by_id == user_model.id
    assert data.default_public_net == pub_net
    assert data.default_private_net == priv_net
    assert data.private_net_proxy_host == proxy_host
    assert data.private_net_proxy_user == proxy_user
    assert data.project == project_model
    assert data.project_id == project_model.id
    assert data.region == region_model
    assert data.region_id == region_model.id


def test_duplicate_override(
    db_session: Session,
    user_model: User,
    project_model: Project,
    region_model: Region,
):
    """Faili in creating a second overrides on the same entities."""
    data1 = RegionOverrides(
        created_by=user_model,
        updated_by=user_model,
        default_public_net="Name1",
        project=project_model,
        region=region_model,
    )
    data2 = RegionOverrides(
        created_by=user_model,
        updated_by=user_model,
        default_public_net="Name2",
        project=project_model,
        region=region_model,
    )
    db_session.add(data1)
    db_session.add(data2)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match="UNIQUE constraint failed: regionoverrides.region_id, "
        "regionoverrides.project_id",
    ):
        db_session.commit()
