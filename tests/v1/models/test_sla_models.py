"""Test suite for the SLA model, verifying fields, types, and relationships."""

import uuid
from datetime import date, datetime

import pytest
import sqlalchemy.exc
from pydantic import AnyHttpUrl
from sqlmodel import Session

from fed_mgr.v1.identity_providers.user_groups.slas.schemas import SLABase
from fed_mgr.v1.models import SLA, Project, User, UserGroup
from fed_mgr.v1.schemas import CreationTime, ItemID, UpdateTime


def test_sla_model(
    db_session: Session, user_model: User, user_group_model: UserGroup
) -> None:
    """Verify SLA model fields, types and relationships.

    The test constructs an `SLA` instance attached to a `UserGroup`, sets
    date ranges and a URL, persists it and asserts the expected types and
    relationship wiring are present.
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
    db_session.commit()

    assert isinstance(sla, ItemID)
    assert isinstance(sla, CreationTime)
    assert isinstance(sla, UpdateTime)
    assert isinstance(sla, SLABase)
    assert isinstance(sla.id, uuid.UUID)
    assert isinstance(sla.created_at, datetime)
    assert isinstance(sla.updated_at, datetime)
    assert sla.created_by == user_model
    assert sla.created_by_id == user_model.id
    assert sla.updated_by == user_model
    assert sla.updated_by_id == user_model.id
    assert isinstance(sla.url, AnyHttpUrl)
    assert sla.url == AnyHttpUrl(url)
    assert sla.name == name
    assert sla.description == desc
    assert isinstance(sla.start_date, date)
    assert sla.start_date == start_date
    assert isinstance(sla.end_date, date)
    assert sla.end_date == end_date
    assert sla.user_group == user_group_model
    assert sla.user_group.id == user_group_model.id
    assert sla.projects == []

    assert user_model.created_slas == [sla]
    assert user_model.updated_slas == [sla]


def test_duplicate_user_group(
    db_session: Session, user_model: User, sla_model: SLA, project_model: Project
) -> None:
    """Ensure unique constraint prevents duplicate group names per IDP.

    Creating a second UserGroup with the same name under the same identity
    provider should raise an IntegrityError on commit.
    """
    name = "Test SLA2"
    start_date = date(2025, 1, 1)
    end_date = date(2026, 1, 1)
    user = SLA(
        created_by=user_model,
        updated_by=user_model,
        name=name,
        start_date=start_date,
        end_date=end_date,
        url=sla_model.url,
        user_group=sla_model.user_group,
    )
    db_session.add(user)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError, match="UNIQUE constraint failed: sla.url"
    ):
        db_session.commit()


def test_delete_fail_still_slas(
    db_session: Session, sla_model: SLA, project_model: Project
) -> None:
    """Can't exist idp with same endpoint."""
    sla_model.projects.append(project_model)
    db_session.add(sla_model)
    db_session.commit()

    db_session.delete(sla_model)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError, match="FOREIGN KEY constraint failed"
    ):
        db_session.commit()
