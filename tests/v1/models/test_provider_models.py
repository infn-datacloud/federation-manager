"""Unit tests for provider schemas in fed_mgr.v1.providers.

This module contains unit tests that validate the SQLModel-backed `Provider`
model and its associated schema behaviour. Tests verify:

- Presence of audit mixins (ID, creation/update timestamps)
- Field types and coercions (e.g. `auth_endpoint` to AnyHttpUrl)
- Relationship containers (idps, regions, projects)
- Default empty-list values and root_project behavior

Fixtures used:
    - db_session: transactional SQLModel session scoped to a test
    - user_model: a persisted User instance used as creator/updater
"""

import uuid
from datetime import datetime

from pydantic import AnyHttpUrl
from sqlmodel import Session

from fed_mgr.v1.models import Provider, User
from fed_mgr.v1.providers.schemas import ProviderBase
from fed_mgr.v1.schemas import CreationTime, ItemID, UpdateTime
from tests.utils import random_lower_string


def test_provider_model(db_session: Session, user_model: User) -> None:
    """Verify Provider model fields, types and relationships.

    The test constructs a `Provider` instance with sample values, persists it,
    and asserts that mixins, typed fields and relationships are present and in
    the expected initial state.
    """
    name = "foo"
    desc = "desc"
    type = "openstack"
    auth_endpoint = "https://example.com/auth"
    is_pub = True
    emails = ["admin@example.com"]
    provider = Provider(
        created_by=user_model,
        updated_by=user_model,
        name=name,
        description=desc,
        type=type,
        auth_endpoint=auth_endpoint,
        is_public=is_pub,
        support_emails=emails,
        rally_username=random_lower_string(),
        rally_password=random_lower_string(),
        site_admins=[user_model],
    )
    db_session.add(provider)
    db_session.commit()

    assert isinstance(provider, ItemID)
    assert isinstance(provider, CreationTime)
    assert isinstance(provider, UpdateTime)
    assert isinstance(provider, ProviderBase)
    assert isinstance(provider.id, uuid.UUID)
    assert isinstance(provider.created_at, datetime)
    assert isinstance(provider.updated_at, datetime)
    assert provider.created_by == user_model
    assert provider.created_by_id == user_model.id
    assert provider.updated_by == user_model
    assert provider.updated_by_id == user_model.id
    assert isinstance(provider.auth_endpoint, AnyHttpUrl)
    assert provider.auth_endpoint == AnyHttpUrl(auth_endpoint)
    assert provider.name == name
    assert provider.type == type
    assert provider.is_public == is_pub
    assert provider.support_emails == emails
    assert provider.rally_username is not None
    assert provider.rally_password is not None
    assert provider.image_tags == []
    assert provider.network_tags == []
    assert provider.site_admins == [user_model]
    assert provider.site_testers == []
    assert provider.idps == []
    assert provider.regions == []
    assert provider.projects == []
    assert provider.root_project is None

    assert user_model.created_providers == [provider]
    assert user_model.updated_providers == [provider]
    assert user_model.owned_providers == [provider]
