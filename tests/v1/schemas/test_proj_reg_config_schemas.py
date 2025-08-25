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
from unittest.mock import MagicMock

from pydantic import AnyHttpUrl

from fed_mgr.v1.models import RegionOverrides
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
    CreationTime,
    EditableQuery,
    EditableRead,
    PaginationQuery,
    SortQuery,
    UpdateTime,
)

DUMMY_ENDPOINT = "https://example.com/regions"
DUMMY_PUB_NET = "pub-net"
DUMMY_PRIV_NET = "priv-net"
DUMMY_PROXY_HOST = "192.168.1.1:1234"
DUMMY_PROXY_USER = "my-user"


def test_proj_reg_config_model():
    """Test ProjRegConnection model fields."""
    creator = MagicMock()
    project = MagicMock()
    region = MagicMock()
    now = datetime.now()
    link = RegionOverrides(
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        default_public_net=DUMMY_PUB_NET,
        default_private_net=DUMMY_PRIV_NET,
        private_net_proxy_host=DUMMY_PROXY_HOST,
        private_net_proxy_user=DUMMY_PROXY_USER,
        project=project,
        region=region,
    )
    assert isinstance(link, CreationTime)
    assert isinstance(link, UpdateTime)
    assert link.created_at == now
    assert link.created_by == creator
    assert link.updated_at == now
    assert link.updated_by == creator
    assert link.default_public_net == DUMMY_PUB_NET
    assert link.default_private_net == DUMMY_PRIV_NET
    assert link.private_net_proxy_host == DUMMY_PROXY_HOST
    assert link.private_net_proxy_user == DUMMY_PROXY_USER
    assert link.project == project
    assert link.region == region


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
    assert isinstance(read, CreationRead)
    assert isinstance(read, EditableRead)
    assert isinstance(read.links, ProjRegConnectionLinks)


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
        resource_url=AnyHttpUrl("https://api.com/prov/proj/regions"),
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
        default_public_net=DUMMY_PUB_NET,
        default_private_net=DUMMY_PRIV_NET,
        private_net_proxy_host=DUMMY_PROXY_HOST,
        private_net_proxy_user=DUMMY_PROXY_USER,
    )
    assert query.region_id == "region"
    assert query.default_public_net == DUMMY_PUB_NET
    assert query.default_private_net == DUMMY_PRIV_NET
    assert query.private_net_proxy_host == DUMMY_PROXY_HOST
    assert query.private_net_proxy_user == DUMMY_PROXY_USER
