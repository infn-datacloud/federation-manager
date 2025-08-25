"""Unit tests for fed_mgr.v1.identity_providers.schemas.

Tests in this file:
- test_identity_provider_base_fields
- test_identity_provider_inheritance
- test_identity_provider_list
- test_identity_provider_create_is_base
- test_identity_provider_query_defaults
- test_identity_provider_query_with_values
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

from pydantic import AnyHttpUrl

from fed_mgr.v1.identity_providers.schemas import (
    IdentityProviderBase,
    IdentityProviderCreate,
    IdentityProviderLinks,
    IdentityProviderList,
    IdentityProviderQuery,
    IdentityProviderRead,
)
from fed_mgr.v1.models import IdentityProvider
from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    CreationTime,
    DescriptionQuery,
    EditableQuery,
    EditableRead,
    ItemDescription,
    ItemID,
    PaginationQuery,
    SortQuery,
    UpdateTime,
)

DUMMY_ENDPOINT = "https://example.com"
DUMMY_NAME = "Test IdP"
DUMMY_GROUPS_CLAIM = "groups"
DUMMY_PROTOCOL = "openid"
DUMMY_AUDIENCE = "aud1"
DUMMY_DESC = "A test identity provider."


def test_identity_provider_model():
    """Test IdentityProvider model fields."""
    creator = MagicMock()
    id_ = uuid.uuid4()
    now = datetime.now()
    idp = IdentityProvider(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        description=DUMMY_DESC,
        endpoint=DUMMY_ENDPOINT,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
    )
    assert isinstance(idp, ItemID)
    assert isinstance(idp, CreationTime)
    assert isinstance(idp, UpdateTime)
    assert isinstance(idp, IdentityProviderBase)
    assert idp.id == id_
    assert idp.created_at == now
    assert idp.created_by == creator
    assert idp.updated_at == now
    assert idp.updated_by == creator
    assert isinstance(idp.endpoint, str)
    assert AnyHttpUrl(idp.endpoint) == AnyHttpUrl(DUMMY_ENDPOINT)
    assert idp.name == DUMMY_NAME
    assert idp.description == DUMMY_DESC
    assert idp.groups_claim == DUMMY_GROUPS_CLAIM
    assert idp.protocol == DUMMY_PROTOCOL
    assert idp.audience == DUMMY_AUDIENCE


def test_identity_provider_base_fields():
    """Test IdentityProviderBase field assignment."""
    base = IdentityProviderBase(
        description=DUMMY_DESC,
        endpoint=DUMMY_ENDPOINT,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
    )
    assert isinstance(base, ItemDescription)
    assert base.endpoint == AnyHttpUrl(DUMMY_ENDPOINT)
    assert base.name == DUMMY_NAME
    assert base.groups_claim == DUMMY_GROUPS_CLAIM
    assert base.protocol == DUMMY_PROTOCOL
    assert base.audience == DUMMY_AUDIENCE


def test_identity_provider_create_is_base():
    """Test that IdentityProviderCreate is an instance of IdentityProviderBase."""
    idp_create = IdentityProviderCreate(
        description=DUMMY_DESC,
        endpoint=DUMMY_ENDPOINT,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
    )
    assert isinstance(idp_create, IdentityProviderBase)


def test_identity_provider_links_fields():
    """Test IdentityProviderLinks field assignment."""
    links = IdentityProviderLinks(user_groups=DUMMY_ENDPOINT)
    assert links.user_groups == AnyHttpUrl(DUMMY_ENDPOINT)


def test_identity_provider_read_inheritance():
    """Test IdentityProviderRead inheritance and adds links."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    idp_read = IdentityProviderRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        description=DUMMY_DESC,
        endpoint=DUMMY_ENDPOINT,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
        base_url=DUMMY_ENDPOINT,
    )
    assert isinstance(idp_read, ItemID)
    assert isinstance(idp_read, CreationRead)
    assert isinstance(idp_read, EditableRead)
    assert isinstance(idp_read, IdentityProviderBase)
    assert isinstance(idp_read.links, IdentityProviderLinks)


def test_identity_provider_list():
    """Test IdentityProviderList data field contains list of IdentityProvider."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    idp_read = IdentityProviderRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        description=DUMMY_DESC,
        endpoint=DUMMY_ENDPOINT,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
        base_url=DUMMY_ENDPOINT,
    )
    idp_list = IdentityProviderList(
        data=[idp_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=AnyHttpUrl("https://api.com/idps"),
    )
    assert isinstance(idp_list.data, list)
    assert idp_list.data[0] == idp_read


def test_identity_provider_query_defaults():
    """Test that IdentityProviderQuery initializes all fields to None by default."""
    query = IdentityProviderQuery()
    assert isinstance(query, DescriptionQuery)
    assert isinstance(query, CreationQuery)
    assert isinstance(query, EditableQuery)
    assert isinstance(query, SortQuery)
    assert isinstance(query, PaginationQuery)
    assert query.endpoint is None
    assert query.name is None
    assert query.groups_claim is None
    assert query.protocol is None
    assert query.audience is None


def test_identity_provider_query_with_values():
    """Test that IdentityProviderQuery assigns provided values to its fields."""
    query = IdentityProviderQuery(
        endpoint="idp",
        name="test",
        groups_claim="grp",
        protocol="prot",
        audience="aud",
    )
    assert query.endpoint == "idp"
    assert query.name == "test"
    assert query.groups_claim == "grp"
    assert query.protocol == "prot"
    assert query.audience == "aud"
