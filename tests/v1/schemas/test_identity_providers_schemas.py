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

DUMMY_ENDPOINT = "https://idp.example.com"
DUMMY_NAME = "Test IdP"
DUMMY_GROUPS_CLAIM = "groups"
DUMMY_PROTOCOL = "openid"
DUMMY_AUDIENCE = "aud1"
DUMMY_DESC = "A test identity provider."


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
    assert base.description == DUMMY_DESC
    assert base.endpoint == AnyHttpUrl(DUMMY_ENDPOINT)
    assert base.name == DUMMY_NAME
    assert base.groups_claim == DUMMY_GROUPS_CLAIM
    assert base.protocol == DUMMY_PROTOCOL
    assert base.audience == DUMMY_AUDIENCE


def test_identity_provider_inheritance():
    """Test IdentityProvider inherits and assigns all fields."""
    id_ = uuid.uuid4()
    now = datetime.now()
    provider = IdentityProvider(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        description=DUMMY_DESC,
        endpoint=DUMMY_ENDPOINT,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
    )
    assert provider.id == id_
    assert provider.created_at == now
    assert provider.created_by == id_
    assert provider.updated_at == now
    assert provider.updated_by == id_
    assert AnyHttpUrl(provider.endpoint) == AnyHttpUrl(DUMMY_ENDPOINT)
    assert provider.name == DUMMY_NAME
    assert provider.groups_claim == DUMMY_GROUPS_CLAIM
    assert provider.protocol == DUMMY_PROTOCOL
    assert provider.audience == DUMMY_AUDIENCE


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
    url = AnyHttpUrl(DUMMY_ENDPOINT)
    links = IdentityProviderLinks(user_groups=url)
    assert links.user_groups == url


def test_identity_provider_read_inheritance():
    """Test IdentityProviderRead inherits from IdentityProvider and adds links."""
    id_ = uuid.uuid4()
    now = datetime.now()
    url = AnyHttpUrl(DUMMY_ENDPOINT)
    links = IdentityProviderLinks(user_groups=url)
    idp_read = IdentityProviderRead(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        description=DUMMY_DESC,
        endpoint=DUMMY_ENDPOINT,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
        links=links,
    )
    assert idp_read.id == id_
    assert idp_read.links == links


def test_identity_provider_list():
    """Test IdentityProviderList data field contains list of IdentityProvider."""
    id_ = uuid.uuid4()
    now = datetime.now()
    url = AnyHttpUrl(DUMMY_ENDPOINT)
    links = IdentityProviderLinks(user_groups=url)
    provider = IdentityProviderRead(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        description=DUMMY_DESC,
        endpoint=DUMMY_ENDPOINT,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
        links=links,
    )
    idp_list = IdentityProviderList(
        data=[provider],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=AnyHttpUrl("https://api.com/idps"),
    )
    assert isinstance(idp_list.data, list)
    assert AnyHttpUrl(idp_list.data[0].endpoint) == AnyHttpUrl(DUMMY_ENDPOINT)


def test_identity_provider_query_defaults():
    """Test that IdentityProviderQuery initializes all fields to None by default."""
    query = IdentityProviderQuery()
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
