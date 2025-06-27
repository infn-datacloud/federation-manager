"""Unit tests for provider schemas in fed_mgr.v1.providers."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pydantic import AnyHttpUrl, ValidationError

from fed_mgr.v1.models import Provider
from fed_mgr.v1.providers.schemas import (
    ProviderBase,
    ProviderCreate,
    ProviderLinks,
    ProviderList,
    ProviderQuery,
    ProviderRead,
    ProviderStatus,
    ProviderType,
    ProviderUpdate,
)
from fed_mgr.v1.schemas import (
    Creation,
    CreationQuery,
    DescriptionQuery,
    Editable,
    EditableQuery,
    ItemID,
    PaginationQuery,
    SortQuery,
)

DUMMY_NAME = "foo"
DUMMY_DESC = "desc"
DUMMY_TYPE = ProviderType.openstack
DUMMY_AUTH_ENDPOINT = "https://example.com/auth"
DUMMY_IS_PUB = True
DUMMY_EMAILS = ["admin@example.com"]
DUMMY_ENDPOINT = "https://example.com"


def test_provider_type_enum():
    """Test ProviderType enum values."""
    assert ProviderType.openstack == "openstack"
    assert ProviderType.kubernetes == "kubernetes"


def test_provider_status_enum_all_values():
    """Test all ProviderStatus enum values and their integer representations."""
    status_map = {
        "draft": 0,
        "submitted": 1,
        "ready": 2,
        "evaluation": 3,
        "pre_production": 4,
        "active": 5,
        "deprecated": 6,
        "removed": 7,
        "degraded": 8,
        "maintenance": 9,
        "re_evaluation": 10,
    }
    for name, value in status_map.items():
        enum_member = getattr(ProviderStatus, name)
        assert int(enum_member) == value


def test_identity_provider_model():
    """Test IdentityProvider model fields."""
    id_ = uuid.uuid4()
    now = datetime.now()
    site_admin = MagicMock()
    site_admin.id = uuid.uuid4()
    site_admins = [site_admin]
    provider = Provider(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
        site_admins=site_admins,
    )
    assert isinstance(provider, ItemID)
    assert isinstance(provider, Creation)
    assert isinstance(provider, Editable)
    assert isinstance(provider, ProviderBase)
    assert provider.id == id_
    assert provider.created_at == now
    assert provider.created_by == id_
    assert provider.updated_at == now
    assert provider.updated_by == id_
    assert isinstance(provider.auth_endpoint, str)
    assert AnyHttpUrl(provider.auth_endpoint) == AnyHttpUrl(DUMMY_AUTH_ENDPOINT)
    assert provider.name == DUMMY_NAME
    assert provider.type == DUMMY_TYPE
    assert provider.is_public == DUMMY_IS_PUB
    assert provider.support_emails == DUMMY_EMAILS
    assert provider.image_tags == []
    assert provider.network_tags == []
    assert provider.site_admins == site_admins


def test_provider_base_required_fields():
    """Test ProviderBase requires name, type, auth_endpoint, support_emails."""
    obj = ProviderBase(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
    )
    assert obj.name == DUMMY_NAME
    assert obj.type == DUMMY_TYPE
    assert obj.auth_endpoint == AnyHttpUrl(DUMMY_AUTH_ENDPOINT)
    assert obj.is_public == DUMMY_IS_PUB
    assert obj.support_emails == DUMMY_EMAILS
    assert obj.image_tags == []
    assert obj.network_tags == []


def test_provider_base_support_emails_empty():
    """Test ProviderBase support_emails must not be empty."""
    with pytest.raises(ValidationError):
        ProviderBase(
            name=DUMMY_NAME,
            description=DUMMY_DESC,
            type=DUMMY_TYPE,
            auth_endpoint=DUMMY_AUTH_ENDPOINT,
            is_public=DUMMY_IS_PUB,
            support_emails=[],
        )


def test_provider_base_image_network_tags():
    """Test ProviderBase image_tags and network_tags default to empty list."""
    obj = ProviderBase(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
    )
    assert obj.image_tags == []
    assert obj.network_tags == []
    # Custom values
    obj2 = ProviderBase(
        name="bar",
        type=ProviderType.kubernetes,
        auth_endpoint="https://example.com/auth2",
        is_public=False,
        support_emails=["admin2@example.com"],
        image_tags=["img1"],
        network_tags=["net1"],
    )
    assert obj2.image_tags == ["img1"]
    assert obj2.network_tags == ["net1"]


def test_provider_create_is_base():
    """Test that ProviderCreate is an instance of ProviderBase."""
    site_admins = [uuid.uuid4()]
    provider_create = ProviderCreate(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
        site_admins=site_admins,
    )
    assert isinstance(provider_create, ProviderBase)
    assert provider_create.site_admins == site_admins


def test_provider_create_site_admins_empty():
    """Test ProviderCreate site_admins must not be empty."""
    with pytest.raises(ValidationError):
        ProviderCreate(
            name=DUMMY_NAME,
            description=DUMMY_DESC,
            type=DUMMY_TYPE,
            auth_endpoint=DUMMY_AUTH_ENDPOINT,
            is_public=DUMMY_IS_PUB,
            support_emails=DUMMY_EMAILS,
            site_admins=[],
        )


def test_provider_update_default_values():
    """Test ProviderUpdate default fields are all None."""
    obj = ProviderUpdate()
    assert obj.name is None
    assert obj.description is None
    assert obj.auth_endpoint is None
    assert obj.is_public is None
    assert obj.support_emails is None
    assert obj.image_tags is None
    assert obj.network_tags is None
    assert obj.site_admins is None


def test_provider_update_fields():
    """Test fields of ProviderUpdate accept same values of ProviderCreate."""
    site_admins = [uuid.uuid4()]
    obj = ProviderUpdate(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
        image_tags=["img1"],
        network_tags=["net1"],
        site_admins=site_admins,
    )
    assert obj.name == DUMMY_NAME
    assert obj.auth_endpoint == AnyHttpUrl(DUMMY_AUTH_ENDPOINT)
    assert obj.is_public == DUMMY_IS_PUB
    assert obj.support_emails == DUMMY_EMAILS
    assert obj.image_tags == ["img1"]
    assert obj.network_tags == ["net1"]
    assert obj.site_admins == site_admins


def test_provider_update_support_emails_empty():
    """Test ProviderUpdate support_emails must not be empty (if not None)."""
    with pytest.raises(ValidationError):
        ProviderUpdate(support_emails=[])


def test_provider_update_site_admins_empty():
    """Test ProviderUpdate site_admins must not be empty (if not None)."""
    with pytest.raises(ValidationError):
        ProviderUpdate(site_admins=[])


def test_provider_links_fields():
    """Test ProviderLinks fields are required and AnyHttpUrl."""
    links = ProviderLinks(
        idps=DUMMY_ENDPOINT, projects=DUMMY_ENDPOINT, regions=DUMMY_ENDPOINT
    )
    assert links.idps == AnyHttpUrl(DUMMY_ENDPOINT)
    assert links.projects == AnyHttpUrl(DUMMY_ENDPOINT)
    assert links.regions == AnyHttpUrl(DUMMY_ENDPOINT)


def test_provider_read_inheritance():
    """Test ProviderRead inherits from Provider and adds links."""
    id_ = uuid.uuid4()
    now = datetime.now()
    site_admin = MagicMock()
    site_admin.id = uuid.uuid4()
    site_admins = [site_admin]
    links = ProviderLinks(
        idps=DUMMY_ENDPOINT, projects=DUMMY_ENDPOINT, regions=DUMMY_ENDPOINT
    )
    provider_read = ProviderRead(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
        site_admins=site_admins,
        links=links,
        status=ProviderStatus.active,
    )
    assert provider_read.links == links
    assert provider_read.status == ProviderStatus.active
    assert provider_read.site_admins == [item.id for item in site_admins]


def test_provider_list():
    """Test ProviderList schema with data list."""
    id_ = uuid.uuid4()
    now = datetime.now()
    site_admin = MagicMock()
    site_admin.id = uuid.uuid4()
    site_admins = [site_admin]
    links = ProviderLinks(
        idps=DUMMY_ENDPOINT, projects=DUMMY_ENDPOINT, regions=DUMMY_ENDPOINT
    )
    read = ProviderRead(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
        site_admins=site_admins,
        links=links,
        status=ProviderStatus.active,
    )
    plist = ProviderList(
        data=[read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=AnyHttpUrl("https://api.com/providers"),
    )
    assert isinstance(plist.data, list)
    assert plist.data[0] == read


def test_provider_query_defaults():
    """Test that ProviderQuery initializes all fields to None by default."""
    query = ProviderQuery()
    assert isinstance(query, DescriptionQuery)
    assert isinstance(query, CreationQuery)
    assert isinstance(query, EditableQuery)
    assert isinstance(query, SortQuery)
    assert isinstance(query, PaginationQuery)
    assert query.name is None
    assert query.name is None
    assert query.type is None
    assert query.auth_endpoint is None
    assert query.is_public is None
    assert query.support_emails is None
    assert query.image_tags is None
    assert query.network_tags is None
    assert query.status is None
    assert query.site_admins is None


def test_provider_query_with_values():
    """Test that ProviderQuery assigns provided values to its fields."""
    query = ProviderQuery(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type="openstack",
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails="admin@example.com",
        image_tags="img1",
        network_tags="net1",
        status="active",
        site_admins="id1",
    )
    assert query.name == DUMMY_NAME
    assert query.type == "openstack"
    assert query.auth_endpoint == DUMMY_AUTH_ENDPOINT
    assert query.is_public is DUMMY_IS_PUB
    assert query.support_emails == "admin@example.com"
    assert query.image_tags == "img1"
    assert query.network_tags == "net1"
    assert query.status == "active"
    assert query.site_admins == "id1"
