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

from pydantic import AnyHttpUrl

from fed_mgr.v1.identity_providers.user_groups.slas.schemas import (
    SLABase,
    SLACreate,
    SLALinks,
    SLAList,
    SLAQuery,
    SLARead,
)
from fed_mgr.v1.models import SLA

DUMMY_NAME = "Test SLA"
DUMMY_DESC = "desc"
DUMMY_URL = "https://sla.example.com"
DUMMY_START_DATE = date(2024, 1, 1)
DUMMY_END_DATE = date(2025, 1, 1)


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
    assert base.description == DUMMY_DESC
    assert base.url == AnyHttpUrl(DUMMY_URL)
    assert base.start_date == DUMMY_START_DATE
    assert base.end_date == DUMMY_END_DATE


def test_sla_inheritance():
    """Test SLA inherits and assigns all fields."""
    id_ = uuid.uuid4()
    now = datetime.now()
    user_group_id = uuid.uuid4()
    sla = SLA(
        id=id_,
        created_at=now,
        created_by=id_,
        updated_at=now,
        updated_by=id_,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        url=DUMMY_URL,
        start_date=DUMMY_START_DATE,
        end_date=DUMMY_END_DATE,
        user_group_id=user_group_id,
    )
    assert sla.id == id_
    assert sla.created_at == now
    assert sla.created_by == id_
    assert sla.updated_at == now
    assert sla.updated_by == id_
    assert sla.user_group_id == user_group_id
    assert sla.name == DUMMY_NAME
    assert AnyHttpUrl(sla.url) == AnyHttpUrl(DUMMY_URL)


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


def test_sla_links_fields():
    """Test SLALinks field assignment."""
    url = AnyHttpUrl("https://api.com/projects")
    links = SLALinks(projects=url)
    assert links.projects == url


def test_sla_read_inheritance():
    """Test SLARead inherits from SLA and adds links."""
    id_ = uuid.uuid4()
    url = AnyHttpUrl("https://api.com/projects")
    links = SLALinks(projects=url)
    sla_read = SLARead(
        id=id_,
        created_at=datetime.now(),
        created_by=id_,
        updated_at=datetime.now(),
        updated_by=id_,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        url=DUMMY_URL,
        start_date=DUMMY_START_DATE,
        end_date=DUMMY_END_DATE,
        links=links,
    )
    assert sla_read.id == id_
    assert sla_read.links == links


def test_sla_list():
    """Test SLAList data field contains list of SLARead."""
    id_ = uuid.uuid4()
    url = AnyHttpUrl("https://api.com/projects")
    links = SLALinks(projects=url)
    sla_read = SLARead(
        id=id_,
        created_at=datetime.now(),
        created_by=id_,
        updated_at=datetime.now(),
        updated_by=id_,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        url=DUMMY_URL,
        start_date=DUMMY_START_DATE,
        end_date=DUMMY_END_DATE,
        links=links,
    )
    sla_list = SLAList(
        data=[sla_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=AnyHttpUrl("https://api.com/slas"),
    )
    assert isinstance(sla_list.data, list)
    assert sla_list.data[0].id == id_


def test_sla_query_defaults():
    """Test that SLAQuery initializes all fields to None by default."""
    query = SLAQuery()
    assert query.name is None
    assert query.url is None
    assert query.start_before is None
    assert query.start_after is None
    assert query.end_before is None
    assert query.end_after is None


def test_sla_query_with_values():
    """Test that SLAQuery assigns provided values to its fields."""
    dt = datetime(2024, 1, 1)
    query = SLAQuery(
        name="sla",
        url=DUMMY_URL,
        start_before=dt,
        start_after=dt,
        end_before=dt,
        end_after=dt,
    )
    assert query.name == "sla"
    assert query.url == DUMMY_URL
    assert query.start_before == dt
    assert query.start_after == dt
    assert query.end_before == dt
    assert query.end_after == dt
