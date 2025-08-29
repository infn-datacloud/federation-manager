"""Unit tests for fed_mgr.v1.providers.regions.schemas.

Tests in this file:
- test_region_base_fields
- test_region_create_inheritance
- test_region_links_fields
- test_region_read_inheritance
- test_region_list_structure
- test_region_query_defaults
- test_region_query_with_values
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

from fed_mgr.v1.models import Region
from fed_mgr.v1.providers.regions.schemas import (
    RegionBase,
    RegionCreate,
    RegionList,
    RegionQuery,
    RegionRead,
)
from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    CreationTime,
    DescriptionQuery,
    EditableQuery,
    EditableRead,
    ItemDescription,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
    UpdateTime,
)


def test_region_model():
    """Test Region model fields."""
    creator = MagicMock()
    id_ = uuid.uuid4()
    now = datetime.now()
    provider = MagicMock()
    region = Region(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name="eu-west-1",
        description="EU West 1",
        provider=provider,
    )
    assert isinstance(region, ItemID)
    assert isinstance(region, CreationTime)
    assert isinstance(region, UpdateTime)
    assert isinstance(region, RegionBase)
    assert region.id == id_
    assert region.created_at == now
    assert region.created_by == creator
    assert region.updated_at == now
    assert region.updated_by == creator
    assert region.name == "eu-west-1"
    assert region.description == "EU West 1"
    assert region.provider == provider


def test_region_base_fields():
    """Test RegionBase field assignment and types."""
    base = RegionBase(name="eu-west-1", description="EU West 1")
    assert isinstance(base, ItemDescription)
    assert base.name == "eu-west-1"
    assert base.description == "EU West 1"


def test_region_create_inheritance():
    """Test RegionCreate inherits from RegionBase and adds location_id."""
    region = RegionCreate(name="eu-west-2", description="desc")
    assert isinstance(region, RegionBase)


def test_region_read_inheritance():
    """Test RegionRead inheritance and adds links."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    region = RegionRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name="eu-central-1",
        description="desc",
    )
    assert isinstance(region, ItemID)
    assert isinstance(region, CreationRead)
    assert isinstance(region, EditableRead)
    assert isinstance(region, RegionBase)
    assert region.name == "eu-central-1"
    assert region.description == "desc"


def test_region_list_structure():
    """Test RegionList data field contains list of RegionRead."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    region_read = RegionRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name="eu-north-1",
        description="desc",
    )
    region_list = RegionList(
        data=[region_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url="https://api.com/regions",
    )
    assert isinstance(region_list, PaginatedList)
    assert isinstance(region_list.data, list)
    assert region_list.data[0] == region_read


def test_region_query_defaults():
    """Test RegionQuery initializes all fields to None by default."""
    query = RegionQuery()
    assert isinstance(query, DescriptionQuery)
    assert isinstance(query, CreationQuery)
    assert isinstance(query, EditableQuery)
    assert isinstance(query, SortQuery)
    assert isinstance(query, PaginationQuery)
    assert query.name is None


def test_region_query_with_values():
    """Test RegionQuery assigns provided values to its fields."""
    query = RegionQuery(name="eu-west-3")
    assert query.name == "eu-west-3"
