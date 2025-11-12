"""Unit tests for the user Pydantic schemas in `fed_mgr.v1.users.schemas`.

This module verifies the core `User` model and related schema behaviour.
Tests cover:

- Validation and coercion of typed fields (for example, `issuer` -> AnyHttpUrl).
- Inheritance from base schemas and presence of ID / creation-time mixins.
- Database uniqueness constraints (scoped to issuer).
- Default/empty relationship containers on a freshly created User.

Fixtures used (from `tests/conftest.py`):
    - `db_session`: transactional SQLModel session for each test
    - `user_model`: a persisted User used by duplication/uniqueness tests
"""

import uuid
from datetime import datetime

import pytest
import sqlalchemy.exc
from pydantic import AnyHttpUrl
from sqlmodel import Session

from fed_mgr.v1.models import (
    IdentityProvider,
    IdpOverrides,
    Project,
    Provider,
    Region,
    RegionOverrides,
    User,
)
from fed_mgr.v1.schemas import CreationTime, ItemID


def test_user_model(db_session: Session) -> None:
    """Validate User model inheritance and core fields.

    Constructs a `User` instance and persists it. The test asserts that the
    model contains the expected ID and creation-time mixins, that typed
    fields (issuer) are coerced properly, and that all empty relationship
    containers are initialized.
    """
    sub = "user-123"
    name = "John Doe"
    email = "john.doe@example.com"
    issuer = "https://issuer.example.com"
    user = User(sub=sub, name=name, email=email, issuer=issuer)
    db_session.add(user)
    db_session.commit()

    assert isinstance(user, ItemID)
    assert isinstance(user, CreationTime)
    assert isinstance(user.id, uuid.UUID)
    assert isinstance(user.created_at, datetime)
    assert user.sub == sub
    assert user.name == name
    assert user.email == email
    assert isinstance(user.issuer, AnyHttpUrl)
    assert user.issuer == AnyHttpUrl(issuer)
    assert user.created_idps == []
    assert user.created_user_groups == []
    assert user.created_slas == []
    assert user.created_providers == []
    assert user.created_regions == []
    assert user.created_projects == []
    assert user.created_prov_idp_conns == []
    assert user.created_proj_reg_configs == []
    assert user.updated_idps == []
    assert user.updated_user_groups == []
    assert user.updated_slas == []
    assert user.updated_providers == []
    assert user.updated_regions == []
    assert user.updated_projects == []
    assert user.updated_prov_idp_conns == []
    assert user.updated_proj_reg_configs == []
    assert user.owned_providers == []
    assert user.assigned_providers == []


def test_duplicate_user(db_session: Session, user_model: User) -> None:
    """Ensure unique constraint prevents duplicate users for the same issuer.

    Creating a second User with the same `sub` and `issuer` should raise an
    IntegrityError on commit.
    """
    user = User(
        sub=user_model.sub,
        name="Duplicate User",
        email="another@email.com",
        issuer=user_model.issuer,
    )
    db_session.add(user)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match="UNIQUE constraint failed: user.sub, user.issuer",
    ):
        db_session.commit()


def test_same_user_different_issuer(db_session: Session, user_model: User) -> None:
    """Verify that users with the same `sub` can exist under different issuers.

    The test creates a User with the same `sub` but a different `issuer`
    and expects successful persistence because uniqueness is scoped to the
    (sub, issuer) pair.
    """
    user = User(
        sub=user_model.sub,
        name=user_model.name,
        email=user_model.email,
        issuer="https://another.issuer.com",
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.id != user_model.id


@pytest.mark.parametrize(
    "model",
    [
        "idp_model",
        "user_group_model",
        "sla_model",
        "provider_model",
        "region_model",
        "project_model",
    ],
)
def test_delete_fail_still_created_item(
    request: pytest.FixtureRequest, db_session: Session, model: str
) -> None:
    """Verify that users with the same `sub` can exist under different issuers.

    The test creates a User with the same `sub` but a different `issuer`
    and expects successful persistence because uniqueness is scoped to the
    (sub, issuer) pair.
    """
    model = request.getfixturevalue(model)
    db_session.commit()

    db_session.delete(model.created_by)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match=r"NOT NULL constraint failed: ([a-zA-Z_][a-zA-Z0-9_]*)\.created_by_id",
    ):
        db_session.commit()


@pytest.mark.parametrize(
    "model",
    [
        "idp_model",
        "user_group_model",
        "sla_model",
        "provider_model",
        "region_model",
        "project_model",
    ],
)
def test_delete_fail_still_updated_item(
    request: pytest.FixtureRequest, db_session: Session, model: str
) -> None:
    """Verify that users with the same `sub` can exist under different issuers.

    The test creates a User with the same `sub` but a different `issuer`
    and expects successful persistence because uniqueness is scoped to the
    (sub, issuer) pair.
    """
    sub = "user-123"
    name = "John Doe"
    email = "john.doe@example.com"
    another_user = User(
        sub=sub, name=name, email=email, issuer="https://another.issuer.com"
    )
    db_session.add(another_user)
    model = request.getfixturevalue(model)
    model.updated_by = another_user
    db_session.add(model)
    db_session.commit()

    db_session.delete(another_user)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match=r"NOT NULL constraint failed: ([a-zA-Z_][a-zA-Z0-9_]*)\.updated_by_id",
    ):
        db_session.commit()


def test_delete_fail_still_created_idp_overrides(
    db_session: Session,
    user_model: User,
    idp_model: IdentityProvider,
    provider_model: Provider,
) -> None:
    """Verify that users with the same `sub` can exist under different issuers.

    The test creates a User with the same `sub` but a different `issuer`
    and expects successful persistence because uniqueness is scoped to the
    (sub, issuer) pair.
    """
    overrides = IdpOverrides(
        created_by=user_model,
        updated_by=user_model,
        idp=idp_model,
        provider=provider_model,
    )
    db_session.add(overrides)
    db_session.commit()

    db_session.delete(overrides.created_by)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match=r"NOT NULL constraint failed: ([a-zA-Z_][a-zA-Z0-9_]*)\.created_by_id",
    ):
        db_session.commit()


def test_delete_fail_still_updated_idp_overrides(
    db_session: Session,
    user_model: User,
    idp_model: IdentityProvider,
    provider_model: Provider,
) -> None:
    """Verify that users with the same `sub` can exist under different issuers.

    The test creates a User with the same `sub` but a different `issuer`
    and expects successful persistence because uniqueness is scoped to the
    (sub, issuer) pair.
    """
    sub = "user-123"
    name = "John Doe"
    email = "john.doe@example.com"
    another_user = User(
        sub=sub, name=name, email=email, issuer="https://another.issuer.com"
    )
    db_session.add(another_user)
    overrides = IdpOverrides(
        created_by=user_model,
        updated_by=another_user,
        idp=idp_model,
        provider=provider_model,
    )
    db_session.add(overrides)
    db_session.commit()

    db_session.delete(another_user)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match=r"NOT NULL constraint failed: ([a-zA-Z_][a-zA-Z0-9_]*)\.updated_by_id",
    ):
        db_session.commit()


def test_delete_fail_still_created_region_overrides(
    db_session: Session,
    user_model: User,
    region_model: Region,
    project_model: Project,
) -> None:
    """Verify that users with the same `sub` can exist under different issuers.

    The test creates a User with the same `sub` but a different `issuer`
    and expects successful persistence because uniqueness is scoped to the
    (sub, issuer) pair.
    """
    overrides = RegionOverrides(
        created_by=user_model,
        updated_by=user_model,
        region=region_model,
        project=project_model,
    )
    db_session.add(overrides)
    db_session.commit()

    db_session.delete(overrides.created_by)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match=r"NOT NULL constraint failed: ([a-zA-Z_][a-zA-Z0-9_]*)\.created_by_id",
    ):
        db_session.commit()


def test_delete_fail_still_updated_region_overrides(
    db_session: Session,
    user_model: User,
    region_model: Region,
    project_model: Project,
) -> None:
    """Verify that users with the same `sub` can exist under different issuers.

    The test creates a User with the same `sub` but a different `issuer`
    and expects successful persistence because uniqueness is scoped to the
    (sub, issuer) pair.
    """
    sub = "user-123"
    name = "John Doe"
    email = "john.doe@example.com"
    another_user = User(
        sub=sub, name=name, email=email, issuer="https://another.issuer.com"
    )
    db_session.add(another_user)
    overrides = RegionOverrides(
        created_by=user_model,
        updated_by=another_user,
        region=region_model,
        project=project_model,
    )
    db_session.add(overrides)
    db_session.commit()

    db_session.delete(another_user)
    with pytest.raises(
        sqlalchemy.exc.IntegrityError,
        match=r"NOT NULL constraint failed: ([a-zA-Z_][a-zA-Z0-9_]*)\.updated_by_id",
    ):
        db_session.commit()
