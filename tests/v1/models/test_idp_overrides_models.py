"""Unit tests for IdP overrides model (IdpOverrides).

This module contains unit tests that verify the SQLModel-backed `IdpOverrides`
model which represents provider-specific overrides for an Identity Provider
relationship. Tests check:

- Presence and types of timestamp mixins (creation/update times)
- Relationship linkage to `Provider` and `IdentityProvider` models
- Field values are persisted and retrievable via the session

Fixtures used:
    - db_session: transactional SQLModel session scoped to a test
    - user_model: a sample persisted User acting as creator/updater
    - provider_model: a sample Provider instance
    - idp_model: a sample IdentityProvider instance
"""

from datetime import datetime

from sqlmodel import Session

from fed_mgr.v1.models import IdentityProvider, IdpOverrides, Provider, User
from fed_mgr.v1.schemas import CreationTime, UpdateTime


def test_idp_overrides_model(
    db_session: Session,
    user_model: User,
    provider_model: Provider,
    idp_model: IdentityProvider,
):
    """Verify IdpOverrides fields, relationships and mixins.

    The fixture creates an `IdpOverrides` instance linking a provider and an
    identity provider, adds it to the session and commits. Assertions verify
    that timestamp mixins are present, relationship foreign keys are set, and
    the provided field values are preserved.
    """
    name = "Test IdP"
    groups_claim = "groups"
    protocol = "openid"
    audience = "aud1"
    data = IdpOverrides(
        created_by=user_model,
        updated_by=user_model,
        name=name,
        groups_claim=groups_claim,
        protocol=protocol,
        audience=audience,
        provider=provider_model,
        idp=idp_model,
    )
    db_session.add(data)
    db_session.commit()

    assert isinstance(data, CreationTime)
    assert isinstance(data, UpdateTime)
    assert isinstance(data, IdpOverrides)
    assert isinstance(data.created_at, datetime)
    assert isinstance(data.updated_at, datetime)
    assert data.created_by == user_model
    assert data.created_by_id == user_model.id
    assert data.updated_by == user_model
    assert data.updated_by_id == user_model.id
    assert data.name == name
    assert data.groups_claim == groups_claim
    assert data.protocol == protocol
    assert data.audience == audience
    assert data.provider == provider_model
    assert data.provider_id == provider_model.id
    assert data.idp == idp_model
    assert data.idp_id == idp_model.id
