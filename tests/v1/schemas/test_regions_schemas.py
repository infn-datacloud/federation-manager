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

import math
import uuid
from datetime import datetime

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
    DescriptionQuery,
    EditableQuery,
    EditableRead,
    ItemDescription,
    ItemID,
    PaginatedList,
    PaginationQuery,
    SortQuery,
)

DUMMY_NAME = "eu-west-1"
DUMMY_DESC = "EU West 1"
DUMMY_ENDPOINT = "https://example.com"
DUMMY_OVERBOOK_CPU = 5.0
DUMMY_OVERBOOK_RAM = 6.0
DUMMY_BANDW_IN = 15.0
DUMMY_BANDW_OUT = 5.0


def test_region_base_fields():
    """Test RegionBase field assignment and types."""
    base = RegionBase(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        overbooking_cpu=DUMMY_OVERBOOK_CPU,
        overbooking_ram=DUMMY_OVERBOOK_RAM,
        bandwidth_in=DUMMY_BANDW_IN,
        bandwidth_out=DUMMY_BANDW_OUT,
    )
    assert isinstance(base, ItemDescription)
    assert base.name == DUMMY_NAME
    assert base.overbooking_cpu == DUMMY_OVERBOOK_CPU
    assert base.overbooking_ram == DUMMY_OVERBOOK_RAM
    assert base.bandwidth_in == DUMMY_BANDW_IN
    assert base.bandwidth_out == DUMMY_BANDW_OUT


def test_region_create_inheritance():
    """Test RegionCreate inherits from RegionBase and adds location_id."""
    region = RegionCreate(name=DUMMY_NAME, description=DUMMY_DESC)
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
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        overbooking_cpu=DUMMY_OVERBOOK_CPU,
        overbooking_ram=DUMMY_OVERBOOK_RAM,
        bandwidth_in=DUMMY_BANDW_IN,
        bandwidth_out=DUMMY_BANDW_OUT,
    )
    assert isinstance(region, ItemID)
    assert isinstance(region, CreationRead)
    assert isinstance(region, EditableRead)
    assert isinstance(region, RegionBase)
    assert region.name == DUMMY_NAME
    assert region.description == DUMMY_DESC
    assert region.overbooking_cpu == DUMMY_OVERBOOK_CPU
    assert region.overbooking_ram == DUMMY_OVERBOOK_RAM
    assert region.bandwidth_in == DUMMY_BANDW_IN
    assert region.bandwidth_out == DUMMY_BANDW_OUT


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
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        overbooking_cpu=DUMMY_OVERBOOK_CPU,
        overbooking_ram=DUMMY_OVERBOOK_RAM,
        bandwidth_in=DUMMY_BANDW_IN,
        bandwidth_out=DUMMY_BANDW_OUT,
    )
    region_list = RegionList(
        data=[region_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=DUMMY_ENDPOINT,
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
    assert query.overbooking_cpu_gte is None
    assert query.overbooking_cpu_lte is None
    assert query.overbooking_ram_gte is None
    assert query.overbooking_ram_lte is None
    assert query.bandwidth_in_gte is None
    assert query.bandwidth_in_lte is None
    assert query.bandwidth_out_gte is None
    assert query.bandwidth_out_lte is None


def test_region_query_with_values():
    """Test RegionQuery assigns provided values to its fields."""
    query = RegionQuery(
        name="eu-west-3",
        overbooking_cpu_gte=1.0,
        overbooking_cpu_lte=2.0,
        overbooking_ram_gte=3.0,
        overbooking_ram_lte=4.0,
        bandwidth_in_gte=5.0,
        bandwidth_in_lte=6.0,
        bandwidth_out_gte=7.0,
        bandwidth_out_lte=8.0,
    )
    assert query.name == "eu-west-3"
    assert math.isclose(query.overbooking_cpu_gte, 1.0)
    assert math.isclose(query.overbooking_cpu_lte, 2.0)
    assert math.isclose(query.overbooking_ram_gte, 3.0)
    assert math.isclose(query.overbooking_ram_lte, 4.0)
    assert math.isclose(query.bandwidth_in_gte, 5.0)
    assert math.isclose(query.bandwidth_in_lte, 6.0)
    assert math.isclose(query.bandwidth_out_gte, 7.0)
    assert math.isclose(query.bandwidth_out_lte, 8.0)
