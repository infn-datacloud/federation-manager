"""Unit tests for fed_mgr.v1.projects.projects.regions.schemas.

Tests in this file:
- test_proj_reg_config_base_fields
- test_proj_reg_config_inheritance
- test_proj_reg_config_list
- test_proj_reg_config_create_is_base
- test_proj_reg_config_query_defaults
- test_proj_reg_config_query_with_values
"""

import uuid
from datetime import datetime

from pydantic import AnyHttpUrl

from fed_mgr.v1 import REGIONS_PREFIX
from fed_mgr.v1.providers.projects.regions.schemas import (
    ProjRegConnectionCreate,
    ProjRegConnectionLinks,
    ProjRegConnectionList,
    ProjRegConnectionQuery,
    ProjRegConnectionRead,
    RegionOverridesBase,
)
from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    EditableQuery,
    EditableRead,
    PaginationQuery,
    SortQuery,
)

DUMMY_ENDPOINT = "https://example.com"
DUMMY_PUB_NET = "pub-net"
DUMMY_PRIV_NET = "priv-net"
DUMMY_PROXY_HOST = "192.168.1.1:1234"
DUMMY_PROXY_USER = "my-user"


def test_proj_reg_config_base_fields():
    """Test ProjRegConnectionBase field assignment."""
    base = RegionOverridesBase(
        default_public_net=DUMMY_PUB_NET,
        default_private_net=DUMMY_PRIV_NET,
        private_net_proxy_host=DUMMY_PROXY_HOST,
        private_net_proxy_user=DUMMY_PROXY_USER,
    )
    assert base.default_public_net == DUMMY_PUB_NET
    assert base.default_private_net == DUMMY_PRIV_NET
    assert base.private_net_proxy_host == DUMMY_PROXY_HOST
    assert base.private_net_proxy_user == DUMMY_PROXY_USER

    base = RegionOverridesBase()
    assert base.default_public_net is None
    assert base.default_private_net is None
    assert base.private_net_proxy_host is None
    assert base.private_net_proxy_user is None


def test_proj_reg_config_create_is_base():
    """Test ProjRegConnectionCreate is an instance of ProjRegConnectionBase."""
    reg_id = uuid.uuid4()
    overrides = {
        "default_public_net": DUMMY_PUB_NET,
        "default_private_net": DUMMY_PRIV_NET,
        "private_net_proxy_host": DUMMY_PROXY_HOST,
        "private_net_proxy_user": DUMMY_PROXY_USER,
    }
    create = ProjRegConnectionCreate(region_id=reg_id, overrides=overrides)
    assert create.region_id == reg_id
    assert isinstance(create.overrides, RegionOverridesBase)


def test_proj_reg_config_links_fields():
    """Test ProjRegConnectionLinks field assignment."""
    links = ProjRegConnectionLinks(regions=DUMMY_ENDPOINT)
    assert links.regions == AnyHttpUrl(DUMMY_ENDPOINT)


def test_proj_reg_config_read_inheritance():
    """Test ProjRegConnectionRead inheritance and adds links."""
    creator = uuid.uuid4()
    project_id = uuid.uuid4()
    region_id = uuid.uuid4()
    now = datetime.now()
    overrides = {
        "default_public_net": DUMMY_PUB_NET,
        "default_private_net": DUMMY_PRIV_NET,
        "private_net_proxy_host": DUMMY_PROXY_HOST,
        "private_net_proxy_user": DUMMY_PROXY_USER,
    }
    read = ProjRegConnectionRead(
        project_id=project_id,
        region_id=region_id,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        overrides=overrides,
        base_url=DUMMY_ENDPOINT,
    )
    assert isinstance(read, CreationRead)
    assert isinstance(read, EditableRead)
    assert isinstance(read.links, ProjRegConnectionLinks)
    assert read.region_id == region_id
    assert read.overrides == RegionOverridesBase(**overrides)
    assert read.links.regions == AnyHttpUrl(f"{DUMMY_ENDPOINT}{REGIONS_PREFIX}")


def test_proj_reg_config_list():
    """ProjRegConnectionList data contains list of ProjRegConnectionRead."""
    creator = uuid.uuid4()
    project_id = uuid.uuid4()
    region_id = uuid.uuid4()
    now = datetime.now()
    read = ProjRegConnectionRead(
        project_id=project_id,
        region_id=region_id,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        provider_id=uuid.uuid4(),
        overrides={},
        base_url=DUMMY_ENDPOINT,
    )
    region_list = ProjRegConnectionList(
        data=[read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=DUMMY_ENDPOINT,
    )
    assert isinstance(region_list.data, list)
    assert region_list.data[0] == read


def test_proj_reg_config_query_defaults():
    """Test ProjRegConnectionQuery initializes all fields to None by default."""
    query = ProjRegConnectionQuery()
    assert isinstance(query, CreationQuery)
    assert isinstance(query, EditableQuery)
    assert isinstance(query, SortQuery)
    assert isinstance(query, PaginationQuery)
    assert query.region_id is None
    assert query.default_public_net is None
    assert query.default_private_net is None
    assert query.private_net_proxy_host is None
    assert query.private_net_proxy_user is None


def test_proj_reg_config_query_with_values():
    """Test that ProjRegConnectionQuery assigns provided values to its fields."""
    query = ProjRegConnectionQuery(
        region_id="region",
        default_public_net="public",
        default_private_net="private",
        private_net_proxy_host="host",
        private_net_proxy_user="user",
    )
    assert query.region_id == "region"
    assert query.default_public_net == "public"
    assert query.default_private_net == "private"
    assert query.private_net_proxy_host == "host"
    assert query.private_net_proxy_user == "user"
