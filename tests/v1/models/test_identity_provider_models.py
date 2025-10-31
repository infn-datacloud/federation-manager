"""Unit tests for fed_mgr.v1.identity_providers.schemas.

This module contains unit tests that verify the SQLModel-backed
`IdentityProvider` model and its Pydantic/SQLModel schemas. Tests focus on:

- Model field types and defaults
- Inheritance of common schema mixins (ID, creation and update timestamps)
- Relationship containers (linked_providers, user_groups)

Fixtures used:
    - db_session: transactional SQLModel session scoped to a test
    - user_model: a sample persisted User used as creator/updater

The primary test is `test_identity_provider_model` which asserts the expected
field types and basic relationships.
"""

import uuid
from datetime import datetime

from pydantic import AnyHttpUrl
from sqlmodel import Session

from fed_mgr.v1.identity_providers.schemas import IdentityProviderBase
from fed_mgr.v1.models import IdentityProvider, User
from fed_mgr.v1.schemas import CreationTime, ItemID, UpdateTime


def test_identity_provider_model(db_session: Session, user_model: User) -> None:
    """Verify IdentityProvider model field types and relationships.

    The test creates an IdentityProvider instance attached to `user_model`, adds
    it to the session and commits. Assertions verify that the model exposes the
    expected mixins (ID, creation/update timestamps), that typed fields such as
    `endpoint` are coerced to appropriate types, and that relationship list
    attributes are present and initially empty.
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
    db_session.commit()

    assert isinstance(idp, ItemID)
    assert isinstance(idp, CreationTime)
    assert isinstance(idp, UpdateTime)
    assert isinstance(idp, IdentityProviderBase)
    assert isinstance(idp.id, uuid.UUID)
    assert isinstance(idp.created_at, datetime)
    assert isinstance(idp.updated_at, datetime)
    assert idp.created_by == user_model
    assert idp.created_by_id == user_model.id
    assert idp.updated_by == user_model
    assert idp.updated_by_id == user_model.id
    assert isinstance(idp.endpoint, AnyHttpUrl)
    assert idp.endpoint == AnyHttpUrl(endpoint)
    assert idp.name == name
    assert idp.description == desc
    assert idp.groups_claim == groups_claim
    assert idp.protocol == protocol
    assert idp.audience == audience
    assert idp.linked_providers == []
    assert idp.user_groups == []

    assert user_model.created_idps == [idp]
    assert user_model.updated_idps == [idp]
