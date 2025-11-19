"""Unit tests for fed_mgr.v1.providers.projects.schemas.

Tests in this file:
- test_project_base_fields
- test_project_create_inheritance
- test_project_links_fields
- test_project_read_inheritance
- test_project_list_structure
- test_project_query_defaults
- test_project_query_with_values
"""

import uuid
from datetime import datetime

import pytest
from pydantic import AnyHttpUrl

from fed_mgr.v1 import REGIONS_PREFIX
from fed_mgr.v1.providers.projects.schemas import (
    ProjectBase,
    ProjectCreate,
    ProjectLinks,
    ProjectList,
    ProjectQuery,
    ProjectRead,
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

DUMMY_NAME = "project"
DUMMY_DESC = "example desc"
DUMMY_IAAS_ID = "12345"
DUMMY_ENDPOINT = "http://example.com"


def test_project_base_fields():
    """Test ProjectBase field assignment and types."""
    base = ProjectBase(
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        iaas_project_id=DUMMY_IAAS_ID,
        is_root=True,
    )
    assert isinstance(base, ItemDescription)
    assert base.name == DUMMY_NAME
    assert base.description == DUMMY_DESC
    assert base.iaas_project_id == DUMMY_IAAS_ID
    assert base.is_root


def test_project_iaas_id_not_empty():
    """Test ProjectBase field assignment and types."""
    with pytest.raises(ValueError, match="Input value can't be empty string"):
        ProjectBase(name=DUMMY_NAME, description=DUMMY_DESC, iaas_project_id="")


def test_project_create_inheritance():
    """Test ProjectCreate inherits from ProjectBase."""
    project = ProjectCreate(
        name=DUMMY_NAME, description=DUMMY_DESC, iaas_project_id=DUMMY_IAAS_ID
    )
    assert isinstance(project, ProjectBase)


def test_project_links_fields():
    """Test ProjectLinks field assignment and type."""
    links = ProjectLinks(regions=DUMMY_ENDPOINT)
    assert links.regions == AnyHttpUrl(DUMMY_ENDPOINT)


def test_project_read_inheritance():
    """Test ProjectRead inheritance and adds links."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    sla = uuid.uuid4()
    project = ProjectRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        iaas_project_id=DUMMY_IAAS_ID,
        sla=sla,
        base_url=DUMMY_ENDPOINT,
    )
    assert isinstance(project, ItemID)
    assert isinstance(project, CreationRead)
    assert isinstance(project, EditableRead)
    assert isinstance(project, ProjectBase)
    assert isinstance(project.links, ProjectLinks)
    assert project.name == DUMMY_NAME
    assert project.description == DUMMY_DESC
    assert project.iaas_project_id == DUMMY_IAAS_ID
    assert project.sla == sla
    assert project.links.regions == AnyHttpUrl(
        f"{DUMMY_ENDPOINT}/{id_}{REGIONS_PREFIX}"
    )


def test_project_list_structure():
    """Test ProjectList data field contains list of ProjectRead."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    sla = uuid.uuid4()
    project_read = ProjectRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        iaas_project_id=DUMMY_IAAS_ID,
        sla=sla,
        base_url=DUMMY_ENDPOINT,
    )
    project_list = ProjectList(
        data=[project_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=DUMMY_ENDPOINT,
    )
    assert isinstance(project_list, PaginatedList)
    assert isinstance(project_list.data, list)
    assert project_list.data[0] == project_read


def test_project_query_defaults():
    """Test ProjectQuery initializes all fields to None by default."""
    query = ProjectQuery()
    assert isinstance(query, DescriptionQuery)
    assert isinstance(query, CreationQuery)
    assert isinstance(query, EditableQuery)
    assert isinstance(query, SortQuery)
    assert isinstance(query, PaginationQuery)
    assert query.name is None
    assert query.iaas_project_id is None
    assert query.is_root is None
    assert query.sla is None


def test_project_query_with_values():
    """Test ProjectQuery assigns provided values to its fields."""
    sla_id = uuid.uuid4()
    query = ProjectQuery(
        name=DUMMY_NAME, iaas_project_id=DUMMY_IAAS_ID, is_root=True, sla=sla_id
    )
    assert query.name == DUMMY_NAME
    assert query.iaas_project_id == DUMMY_IAAS_ID
    assert query.is_root
    assert query.sla == sla_id
