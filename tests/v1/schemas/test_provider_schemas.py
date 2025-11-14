"""Unit tests for provider schemas in fed_mgr.v1.providers."""

import uuid
from datetime import datetime

import pytest
from pydantic import AnyHttpUrl, ValidationError

from fed_mgr.v1 import IDPS_PREFIX, PROJECTS_PREFIX, REGIONS_PREFIX
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
    CreationQuery,
    CreationRead,
    DescriptionQuery,
    EditableQuery,
    EditableRead,
    ItemID,
    PaginationQuery,
    SortQuery,
)
from tests.utils import random_lower_string

DUMMY_NAME = "foo"
DUMMY_DESC = "desc"
DUMMY_TYPE = ProviderType.openstack
DUMMY_AUTH_ENDPOINT = "https://example.com/auth"
DUMMY_IS_PUB = True
DUMMY_EMAILS = ["admin@example.com"]
DUMMY_IMG_TAGS = ["img1"]
DUMMY_NET_TAGS = ["net1"]
DUMMY_ENDPOINT = "https://example.com"
DUMMY_FLOAT_IPS = True
DUMMY_TEST_NET_ID = "net-id"
DUMMY_TEST_FLAVOR_NAME = "flavor"


def test_provider_type_enum():
    """Test ProviderType enum values."""
    assert ProviderType.openstack == "openstack"
    assert ProviderType.kubernetes == "kubernetes"


def test_provider_status_enum_all_values():
    """Test all ProviderStatus enum values and their integer representations."""
    status_map = {
        "draft": 0,
        "ready": 1,
        "submitted": 2,
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


def test_provider_base_fields():
    """Test ProviderBase requires name, type, auth_endpoint, support_emails."""
    obj = ProviderBase(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
        image_tags=DUMMY_IMG_TAGS,
        network_tags=DUMMY_NET_TAGS,
        rally_username=random_lower_string(),
        rally_password=random_lower_string(),
        floating_ips_enable=DUMMY_FLOAT_IPS,
        test_flavor_name=DUMMY_TEST_FLAVOR_NAME,
        test_network_id=DUMMY_TEST_NET_ID,
    )
    assert obj.name == DUMMY_NAME
    assert obj.type == DUMMY_TYPE
    assert obj.auth_endpoint == AnyHttpUrl(DUMMY_AUTH_ENDPOINT)
    assert obj.is_public == DUMMY_IS_PUB
    assert obj.support_emails == DUMMY_EMAILS
    assert obj.image_tags == DUMMY_IMG_TAGS
    assert obj.network_tags == DUMMY_NET_TAGS
    assert obj.rally_username is not None
    assert obj.rally_password is not None
    assert obj.floating_ips_enable == DUMMY_FLOAT_IPS
    assert obj.test_flavor_name == DUMMY_TEST_FLAVOR_NAME
    assert obj.test_network_id == DUMMY_TEST_NET_ID


def test_provider_base_support_emails_empty():
    """Test ProviderBase support_emails must not be empty."""
    with pytest.raises(ValidationError, match="List must not be empty"):
        ProviderBase(
            name=DUMMY_NAME,
            description=DUMMY_DESC,
            type=DUMMY_TYPE,
            auth_endpoint=DUMMY_AUTH_ENDPOINT,
            is_public=DUMMY_IS_PUB,
            support_emails=[],
            rally_username=random_lower_string(),
            rally_password=random_lower_string(),
        )


def test_provider_create_is_base():
    """Test that ProviderCreate is an instance of ProviderBase."""
    site_admins = [uuid.uuid4()]
    provider_create = ProviderCreate(
        name=DUMMY_NAME,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        support_emails=DUMMY_EMAILS,
        rally_username=random_lower_string(),
        rally_password=random_lower_string(),
        site_admins=site_admins,
    )
    assert isinstance(provider_create, ProviderBase)
    assert provider_create.site_admins == site_admins


def test_provider_create_site_admins_empty():
    """Test ProviderCreate site_admins must not be empty."""
    with pytest.raises(ValidationError, match="List must not be empty"):
        ProviderCreate(
            name=DUMMY_NAME,
            type=DUMMY_TYPE,
            auth_endpoint=DUMMY_AUTH_ENDPOINT,
            support_emails=DUMMY_EMAILS,
            rally_username=random_lower_string(),
            rally_password=random_lower_string(),
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
    assert obj.rally_username is None
    assert obj.rally_password is None
    assert obj.floating_ips_enable is None
    assert obj.test_flavor_name is None
    assert obj.test_network_id is None


def test_provider_update_fields():
    """Test fields of ProviderUpdate accept same values of ProviderCreate."""
    obj = ProviderUpdate(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
        image_tags=DUMMY_IMG_TAGS,
        network_tags=DUMMY_NET_TAGS,
        rally_username=random_lower_string(),
        rally_password=random_lower_string(),
        floating_ips_enable=DUMMY_FLOAT_IPS,
        test_flavor_name=DUMMY_TEST_FLAVOR_NAME,
        test_network_id=DUMMY_TEST_NET_ID,
    )
    assert obj.name == DUMMY_NAME
    assert obj.auth_endpoint == AnyHttpUrl(DUMMY_AUTH_ENDPOINT)
    assert obj.is_public == DUMMY_IS_PUB
    assert obj.support_emails == DUMMY_EMAILS
    assert obj.image_tags == DUMMY_IMG_TAGS
    assert obj.network_tags == DUMMY_NET_TAGS
    assert obj.rally_username is not None
    assert obj.rally_password is not None
    assert obj.floating_ips_enable == DUMMY_FLOAT_IPS
    assert obj.test_flavor_name == DUMMY_TEST_FLAVOR_NAME
    assert obj.test_network_id == DUMMY_TEST_NET_ID


def test_provider_update_support_emails_empty():
    """Test ProviderUpdate support_emails must not be empty (if not None)."""
    with pytest.raises(ValidationError, match="List must not be empty"):
        ProviderUpdate(support_emails=[])


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
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    ids = [uuid.uuid4()]
    provider_read = ProviderRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
        rally_username=random_lower_string(),
        rally_password=random_lower_string(),
        floating_ips_enable=DUMMY_FLOAT_IPS,
        test_flavor_name=DUMMY_TEST_FLAVOR_NAME,
        test_network_id=DUMMY_TEST_NET_ID,
        site_admins=ids,
        site_testers=ids,
        base_url=DUMMY_ENDPOINT,
    )
    assert isinstance(provider_read, ItemID)
    assert isinstance(provider_read, CreationRead)
    assert isinstance(provider_read, EditableRead)
    assert isinstance(provider_read, ProviderRead)
    assert isinstance(provider_read.links, ProviderLinks)
    assert provider_read.links.idps == AnyHttpUrl(
        f"{DUMMY_ENDPOINT}/{id_}{IDPS_PREFIX}"
    )
    assert provider_read.links.regions == AnyHttpUrl(
        f"{DUMMY_ENDPOINT}/{id_}{REGIONS_PREFIX}"
    )
    assert provider_read.links.projects == AnyHttpUrl(
        f"{DUMMY_ENDPOINT}/{id_}{PROJECTS_PREFIX}"
    )
    assert provider_read.status == ProviderStatus.draft
    assert provider_read.site_admins == ids
    assert provider_read.site_testers == ids


def test_provider_list():
    """Test ProviderList schema with data list."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    ids = [uuid.uuid4()]
    read = ProviderRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        type=DUMMY_TYPE,
        auth_endpoint=DUMMY_AUTH_ENDPOINT,
        is_public=DUMMY_IS_PUB,
        support_emails=DUMMY_EMAILS,
        rally_username=random_lower_string(),
        rally_password=random_lower_string(),
        floating_ips_enable=DUMMY_FLOAT_IPS,
        test_flavor_name=DUMMY_TEST_FLAVOR_NAME,
        test_network_id=DUMMY_TEST_NET_ID,
        site_admins=ids,
        site_testers=ids,
        base_url=DUMMY_ENDPOINT,
    )
    plist = ProviderList(
        data=[read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=DUMMY_ENDPOINT,
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
    assert query.site_testers is None
    assert query.rally_username is None
    assert query.floating_ips_enable is None
    assert query.test_flavor_name is None
    assert query.test_network_id is None


def test_provider_query_with_values():
    """Test that ProviderQuery assigns provided values to its fields."""
    ids = [uuid.uuid4()]
    query = ProviderQuery(
        name="foo",
        description="bar",
        type="openstack",
        auth_endpoint="auth",
        is_public=True,
        support_emails="admin@example.com",
        image_tags="img1",
        network_tags="net1",
        status=["active"],
        rally_username="user",
        floating_ips_enable=True,
        test_flavor_name="flavor",
        test_network_id="net_id",
        site_admins=ids,
        site_testers=ids,
    )
    assert query.name == "foo"
    assert query.description == "bar"
    assert query.type == "openstack"
    assert query.auth_endpoint == "auth"
    assert query.is_public
    assert query.support_emails == "admin@example.com"
    assert query.image_tags == "img1"
    assert query.network_tags == "net1"
    assert query.status == ["active"]
    assert query.rally_username == "user"
    assert query.site_admins == ids
    assert query.site_testers == ids
    assert query.floating_ips_enable
    assert query.test_flavor_name == "flavor"
    assert query.test_network_id == "net_id"
