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

from fed_mgr.v1 import USER_GROUPS_PREFIX
from fed_mgr.v1.identity_providers.schemas import (
    IdentityProviderBase,
    IdentityProviderCreate,
    IdentityProviderLinks,
    IdentityProviderList,
    IdentityProviderQuery,
    IdentityProviderRead,
)
from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    DescriptionQuery,
    EditableQuery,
    EditableRead,
    ItemDescription,
    ItemID,
    PaginationQuery,
    SortQuery,
)

DUMMY_ISSUER = "https://issuer.example.com"
DUMMY_NAME = "Test IdP"
DUMMY_GROUPS_CLAIM = "groups"
DUMMY_PROTOCOL = "openid"
DUMMY_AUDIENCE = "aud1"
DUMMY_DESC = "A test identity provider."
DUMMY_ENDPOINT = "https://example.com"


def test_identity_provider_base_fields():
    """Test IdentityProviderBase field assignment."""
    base = IdentityProviderBase(
        description=DUMMY_DESC,
        endpoint=DUMMY_ISSUER,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
    )
    assert isinstance(base, ItemDescription)
    assert isinstance(base.endpoint, AnyHttpUrl)
    assert base.endpoint == AnyHttpUrl(DUMMY_ISSUER)
    assert base.name == DUMMY_NAME
    assert base.groups_claim == DUMMY_GROUPS_CLAIM
    assert base.protocol == DUMMY_PROTOCOL
    assert base.audience == DUMMY_AUDIENCE


def test_identity_provider_create_is_base():
    """Test that IdentityProviderCreate is an instance of IdentityProviderBase."""
    idp_create = IdentityProviderCreate(
        description=DUMMY_DESC,
        endpoint=DUMMY_ISSUER,
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
        endpoint=DUMMY_ISSUER,
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
    assert idp_read.links.user_groups == AnyHttpUrl(
        f"{DUMMY_ENDPOINT}/{id_}{USER_GROUPS_PREFIX}"
    )


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
        endpoint=DUMMY_ISSUER,
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
        resource_url=DUMMY_ENDPOINT,
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
