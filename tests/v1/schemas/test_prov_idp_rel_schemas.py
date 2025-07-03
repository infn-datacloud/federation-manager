"""Unit tests for fed_mgr.v1.providers.identity_providers.schemas.

Tests in this file:
- test_provider_idp_rel_base_fields
- test_provider_idp_rel_inheritance
- test_provider_idp_rel_list
- test_provider_idp_rel_create_is_base
- test_provider_idp_rel_query_defaults
- test_provider_idp_rel_query_with_values
"""

import uuid
from datetime import datetime

from pydantic import AnyHttpUrl

from fed_mgr.v1.models import ProviderIdPConnection
from fed_mgr.v1.providers.identity_providers.schemas import (
    ProviderIdPConnectionBase,
    ProviderIdPConnectionCreate,
    ProviderIdPConnectionLinks,
    ProviderIdPConnectionList,
    ProviderIdPConnectionQuery,
    ProviderIdPConnectionRead,
)
from fed_mgr.v1.schemas import (
    Creation,
    CreationQuery,
    Editable,
    EditableQuery,
    PaginationQuery,
    SortQuery,
)

DUMMY_ENDPOINT = "https://example.com"
DUMMY_NAME = "Test IdP"
DUMMY_GROUPS_CLAIM = "groups"
DUMMY_PROTOCOL = "openid"
DUMMY_AUDIENCE = "aud1"


def test_prov_idp_rel_model():
    """Test ProviderIdPConnection model fields."""
    id_ = uuid.uuid4()
    provider_id = uuid.uuid4()
    idp_id = uuid.uuid4()
    now = datetime.now()
    idp = ProviderIdPConnection(
        provider_id=provider_id,
        idp_id=idp_id,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
    )
    assert isinstance(idp, Creation)
    assert isinstance(idp, Editable)
    assert isinstance(idp, ProviderIdPConnectionBase)
    assert idp.provider_id == provider_id
    assert idp.idp_id == idp_id
    assert idp.created_at == now
    assert idp.created_by == id_
    assert idp.updated_at == now
    assert idp.updated_by == id_
    assert idp.name == DUMMY_NAME
    assert idp.groups_claim == DUMMY_GROUPS_CLAIM
    assert idp.protocol == DUMMY_PROTOCOL
    assert idp.audience == DUMMY_AUDIENCE


def test_prov_idp_rel_base_fields():
    """Test ProviderIdPConnectionBase field assignment."""
    base = ProviderIdPConnectionBase(
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
    )
    assert base.name == DUMMY_NAME
    assert base.groups_claim == DUMMY_GROUPS_CLAIM
    assert base.protocol == DUMMY_PROTOCOL
    assert base.audience == DUMMY_AUDIENCE

    base = ProviderIdPConnectionBase()
    assert base.name is None
    assert base.groups_claim is None
    assert base.protocol is None
    assert base.audience is None


def test_prov_idp_rel_create_is_base():
    """Test ProviderIdPConnectionCreate is an instance of ProviderIdPConnectionBase."""
    create = ProviderIdPConnectionCreate(
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
    )
    assert isinstance(create, ProviderIdPConnectionBase)


def test_prov_idp_rel_links_fields():
    """Test ProviderIdPConnectionLinks field assignment."""
    links = ProviderIdPConnectionLinks(idp=DUMMY_ENDPOINT)
    assert links.idp == AnyHttpUrl(DUMMY_ENDPOINT)


def test_prov_idp_rel_read_inheritance():
    """Test ProviderIdPConnectionRead inheritance and adds links."""
    id_ = uuid.uuid4()
    provider_id = uuid.uuid4()
    idp_id = uuid.uuid4()
    now = datetime.now()
    links = ProviderIdPConnectionLinks(idp=DUMMY_ENDPOINT)
    read = ProviderIdPConnectionRead(
        provider_id=provider_id,
        idp_id=idp_id,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
        links=links,
    )
    assert isinstance(read, Creation)
    assert isinstance(read, Editable)
    assert isinstance(read, ProviderIdPConnectionBase)
    assert read.links == links


def test_prov_idp_rel_list():
    """ProviderIdPConnectionList data contains list of ProviderIdPConnectionRead."""
    id_ = uuid.uuid4()
    provider_id = uuid.uuid4()
    idp_id = uuid.uuid4()
    now = datetime.now()
    links = ProviderIdPConnectionLinks(idp=DUMMY_ENDPOINT)
    read = ProviderIdPConnectionRead(
        provider_id=provider_id,
        idp_id=idp_id,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name=DUMMY_NAME,
        groups_claim=DUMMY_GROUPS_CLAIM,
        protocol=DUMMY_PROTOCOL,
        audience=DUMMY_AUDIENCE,
        links=links,
    )
    idp_list = ProviderIdPConnectionList(
        data=[read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=AnyHttpUrl("https://api.com/prov/idps"),
    )
    assert isinstance(idp_list.data, list)
    assert idp_list.data[0] == read


def test_prov_idp_rel_query_defaults():
    """Test ProviderIdPConnectionQuery initializes all fields to None by default."""
    query = ProviderIdPConnectionQuery()
    assert isinstance(query, CreationQuery)
    assert isinstance(query, EditableQuery)
    assert isinstance(query, SortQuery)
    assert isinstance(query, PaginationQuery)
    assert query.idp_id is None
    assert query.name is None
    assert query.groups_claim is None
    assert query.protocol is None
    assert query.audience is None


def test_prov_idp_rel_query_with_values():
    """Test that ProviderIdPConnectionQuery assigns provided values to its fields."""
    query = ProviderIdPConnectionQuery(
        idp_id="idp",
        name="test",
        groups_claim="grp",
        protocol="prot",
        audience="aud",
    )
    assert query.idp_id == "idp"
    assert query.name == "test"
    assert query.groups_claim == "grp"
    assert query.protocol == "prot"
    assert query.audience == "aud"
