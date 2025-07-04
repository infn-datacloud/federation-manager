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

from pydantic import AnyHttpUrl

from fed_mgr.v1.models import Region
from fed_mgr.v1.providers.regions.schemas import (
    RegionBase,
    RegionCreate,
    RegionLinks,
    RegionList,
    RegionQuery,
    RegionRead,
)
from fed_mgr.v1.schemas import (
    Creation,
    CreationQuery,
    DescriptionQuery,
    Editable,
    EditableQuery,
    ItemDescription,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)


def test_region_model():
    """Test Region model fields."""
    id_ = uuid.uuid4()
    now = datetime.now()
    provider_id = uuid.uuid4()
    location_id = uuid.uuid4()
    region = Region(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name="eu-west-1",
        description="EU West 1",
        provider_id=provider_id,
        location_id=location_id,
    )
    assert isinstance(region, ItemID)
    assert isinstance(region, Creation)
    assert isinstance(region, Editable)
    assert isinstance(region, RegionBase)
    assert region.id == id_
    assert region.created_at == now
    assert region.created_by == id_
    assert region.updated_at == now
    assert region.updated_by == id_
    assert region.name == "eu-west-1"
    assert region.description == "EU West 1"
    assert region.provider_id == provider_id
    assert region.location_id == location_id


def test_region_base_fields():
    """Test RegionBase field assignment and types."""
    base = RegionBase(name="eu-west-1", description="EU West 1")
    assert isinstance(base, ItemDescription)
    assert base.name == "eu-west-1"
    assert base.description == "EU West 1"


def test_region_create_inheritance():
    """Test RegionCreate inherits from RegionBase and adds location_id."""
    loc_id = uuid.uuid4()
    region = RegionCreate(name="eu-west-2", description="desc", location_id=loc_id)
    assert isinstance(region, RegionBase)
    assert region.location_id == loc_id


def test_region_links_fields():
    """Test RegionLinks field assignment and type."""
    url = "https://example.com/location"
    links = RegionLinks(location=url)
    assert isinstance(links, RegionLinks)
    assert links.location == AnyHttpUrl(url)


def test_region_read_inheritance():
    """Test RegionRead inheritance and adds links."""
    id_ = uuid.uuid4()
    now = datetime.now()
    links = RegionLinks(location="https://example.com/location")
    region = RegionRead(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name="eu-central-1",
        description="desc",
        links=links,
    )
    assert isinstance(region, ItemID)
    assert isinstance(region, Creation)
    assert isinstance(region, Editable)
    assert isinstance(region, RegionBase)
    assert region.links == links
    assert region.name == "eu-central-1"
    assert region.description == "desc"


def test_region_list_structure():
    """Test RegionList data field contains list of RegionRead."""
    id_ = uuid.uuid4()
    now = datetime.now()
    links = RegionLinks(location="https://example.com/location")
    region_read = RegionRead(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name="eu-north-1",
        description="desc",
        links=links,
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
