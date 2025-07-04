"""Unit tests for fed_mgr.v1.locations.schemas.

Tests in this file:
- test_location_base_fields
- test_location_create_inheritance
- test_location_read_inheritance
- test_location_list_structure
- test_location_query_defaults
- test_location_query_with_values
"""

import uuid
from datetime import datetime

from fed_mgr.v1.locations.schemas import (
    LocationBase,
    LocationCreate,
    LocationList,
    LocationQuery,
    LocationRead,
)
from fed_mgr.v1.models import Location
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


def test_location_model():
    """Test Location model fields."""
    id_ = uuid.uuid4()
    now = datetime.now()
    location = Location(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name="Test Location",
        country="IT",
        lat=45.0,
        lon=9.0,
        description="A test location.",
    )
    assert isinstance(location, ItemID)
    assert isinstance(location, Creation)
    assert isinstance(location, Editable)
    assert isinstance(location, LocationBase)
    assert location.name == "Test Location"
    assert location.country == "IT"
    assert location.lat == 45.0
    assert location.lon == 9.0
    assert location.description == "A test location."


def test_location_base_fields():
    """Test LocationBase field assignment and types."""
    base = LocationBase(
        name="Test Location",
        country="IT",
        lat=45.0,
        lon=9.0,
        description="A test location.",
    )
    assert isinstance(base, ItemDescription)
    assert base.name == "Test Location"
    assert base.country == "IT"
    assert base.lat == 45.0
    assert base.lon == 9.0
    assert base.description == "A test location."


def test_location_create_inheritance():
    """Test LocationCreate inherits from LocationBase."""
    loc = LocationCreate(
        name="Loc", country="FR", lat=48.8, lon=2.3, description="Paris"
    )
    assert isinstance(loc, LocationBase)


def test_location_read_inheritance():
    """Test LocationRead inherits from ItemID, Creation, Editable, LocationBase."""
    id_ = uuid.uuid4()
    now = datetime.now()
    loc = LocationRead(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name="ReadLoc",
        country="DE",
        lat=52.5,
        lon=13.4,
        description="Berlin",
    )
    assert isinstance(loc, ItemID)
    assert isinstance(loc, Creation)
    assert isinstance(loc, Editable)
    assert isinstance(loc, LocationBase)
    assert loc.id == id_
    assert loc.created_at == now
    assert loc.updated_at == now
    assert loc.name == "ReadLoc"
    assert loc.country == "DE"
    assert loc.lat == 52.5
    assert loc.lon == 13.4
    assert loc.description == "Berlin"


def test_location_list_structure():
    """Test LocationList data field contains list of LocationRead."""
    id_ = uuid.uuid4()
    now = datetime.now()
    loc_read = LocationRead(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name="ListLoc",
        country="ES",
        lat=40.4,
        lon=-3.7,
        description="Madrid",
    )
    loc_list = LocationList(
        data=[loc_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url="https://api.com/locations",
    )
    assert isinstance(loc_list, PaginatedList)
    assert isinstance(loc_list.data, list)
    assert loc_list.data[0] == loc_read


def test_location_query_defaults():
    """Test LocationQuery initializes all fields to None by default."""
    query = LocationQuery()
    assert isinstance(query, DescriptionQuery)
    assert isinstance(query, CreationQuery)
    assert isinstance(query, EditableQuery)
    assert isinstance(query, SortQuery)
    assert isinstance(query, PaginationQuery)
    assert query.name is None
    assert query.country is None
    assert query.lat_gte is None
    assert query.lat_lte is None
    assert query.lon_gte is None
    assert query.lon_lte is None


def test_location_query_with_values():
    """Test LocationQuery assigns provided values to its fields."""
    query = LocationQuery(
        name="loc",
        country="IT",
        lat_gte=40.0,
        lat_lte=50.0,
        lon_gte=8.0,
        lon_lte=12.0,
    )
    assert query.name == "loc"
    assert query.country == "IT"
    assert query.lat_gte == 40.0
    assert query.lat_lte == 50.0
    assert query.lon_gte == 8.0
    assert query.lon_lte == 12.0
