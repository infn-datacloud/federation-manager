"""Unit tests for fed_mgr.v1.identity_providers.user_groups.slas.schemas.

Covers:
- SLABase field assignment
- SLA inheritance and field assignment
- SLACreate inheritance
- SLALinks field assignment
- SLARead inheritance and links
- SLAList data field
- SLAQuery defaults and value assignment
"""

import uuid
from datetime import date, datetime

import pytest
from pydantic import AnyHttpUrl

from fed_mgr.v1 import PROJECTS_PREFIX
from fed_mgr.v1.identity_providers.user_groups.slas.schemas import (
    SLABase,
    SLACreate,
    SLALinks,
    SLAList,
    SLAQuery,
    SLARead,
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

DUMMY_NAME = "Test SLA"
DUMMY_DESC = "desc"
DUMMY_URL = "https://target-sla.com"
DUMMY_START_DATE = date(2024, 1, 1)
DUMMY_END_DATE = date(2025, 1, 1)
DUMMY_ENDPOINT = "https://example.com"


def test_sla_base_fields():
    """Test SLABase field assignment."""
    base = SLABase(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        url=DUMMY_URL,
        start_date=DUMMY_START_DATE,
        end_date=DUMMY_END_DATE,
    )
    assert base.name == DUMMY_NAME
    assert isinstance(base.url, AnyHttpUrl)
    assert base.url == AnyHttpUrl(DUMMY_URL)
    assert isinstance(base.start_date, date)
    assert base.start_date == DUMMY_START_DATE
    assert isinstance(base.end_date, date)
    assert base.end_date == DUMMY_END_DATE


def test_sla_create_is_base():
    """Test that SLACreate is an instance of SLABase."""
    sla_create = SLACreate(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        url=DUMMY_URL,
        start_date=DUMMY_START_DATE,
        end_date=DUMMY_END_DATE,
    )
    assert isinstance(sla_create, SLABase)


def test_invalid_dates():
    """Start date must be lower than end date."""
    with pytest.raises(ValueError, match="Start date must be lower than end date"):
        SLACreate(
            name=DUMMY_NAME,
            description=DUMMY_DESC,
            url=DUMMY_URL,
            start_date=DUMMY_END_DATE,
            end_date=DUMMY_START_DATE,
        )


def test_sla_links_fields():
    """Test SLALinks field assignment."""
    links = SLALinks(projects=DUMMY_URL)
    assert links.projects == AnyHttpUrl(DUMMY_URL)


def test_sla_read_inheritance():
    """Test SLARead inherits from SLA and adds links."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    sla_read = SLARead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        url=DUMMY_URL,
        start_date=DUMMY_START_DATE,
        end_date=DUMMY_END_DATE,
        base_url=DUMMY_ENDPOINT,
    )
    assert isinstance(sla_read, ItemID)
    assert isinstance(sla_read, CreationRead)
    assert isinstance(sla_read, EditableRead)
    assert isinstance(sla_read, SLABase)
    assert isinstance(sla_read.links, SLALinks)
    assert sla_read.links.projects == AnyHttpUrl(
        f"{DUMMY_ENDPOINT}/{id_}{PROJECTS_PREFIX}"
    )


def test_sla_list():
    """Test SLAList data field contains list of SLARead."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    sla_read = SLARead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        url=DUMMY_URL,
        start_date=DUMMY_START_DATE,
        end_date=DUMMY_END_DATE,
        base_url=DUMMY_ENDPOINT,
    )
    sla_list = SLAList(
        data=[sla_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=DUMMY_ENDPOINT,
    )
    assert isinstance(sla_list.data, list)
    assert sla_list.data[0] == sla_read


def test_sla_query_defaults():
    """Test that SLAQuery initializes all fields to None by default."""
    query = SLAQuery()
    assert isinstance(query, DescriptionQuery)
    assert isinstance(query, CreationQuery)
    assert isinstance(query, EditableQuery)
    assert isinstance(query, SortQuery)
    assert isinstance(query, PaginationQuery)
    assert query.name is None
    assert query.url is None
    assert query.start_before is None
    assert query.start_after is None
    assert query.end_before is None
    assert query.end_after is None


def test_sla_query_with_values():
    """Test that SLAQuery assigns provided values to its fields."""
    dt = date(2024, 1, 1)
    query = SLAQuery(
        name="sla",
        url="host",
        start_before=dt,
        start_after=dt,
        end_before=dt,
        end_after=dt,
    )
    assert query.name == "sla"
    assert query.url == "host"
    assert query.start_before == dt
    assert query.start_after == dt
    assert query.end_before == dt
    assert query.end_after == dt
