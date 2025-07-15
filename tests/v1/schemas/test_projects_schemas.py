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
from unittest.mock import MagicMock

from pydantic import AnyHttpUrl

from fed_mgr.v1.models import Project
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

DUMMY_NAME = "project"
DUMMY_DESC = "example desc"
DUMMY_IAAS_ID = "12345"


def test_project_model():
    """Test Project model fields."""
    creator = MagicMock()
    id_ = uuid.uuid4()
    now = datetime.now()
    provider = MagicMock()
    project = Project(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        iaas_project_id=DUMMY_IAAS_ID,
        provider=provider,
    )
    assert isinstance(project, ItemID)
    assert isinstance(project, CreationTime)
    assert isinstance(project, UpdateTime)
    assert isinstance(project, ProjectBase)
    assert project.id == id_
    assert project.created_at == now
    assert project.created_by == creator
    assert project.updated_at == now
    assert project.updated_by == creator
    assert project.name == DUMMY_NAME
    assert project.description == DUMMY_DESC
    assert project.iaas_project_id == DUMMY_IAAS_ID
    assert project.provider == provider


def test_project_base_fields():
    """Test ProjectBase field assignment and types."""
    base = ProjectBase(
        name=DUMMY_NAME, description=DUMMY_DESC, iaas_project_id=DUMMY_IAAS_ID
    )
    assert isinstance(base, ItemDescription)
    assert base.name == DUMMY_NAME
    assert base.description == DUMMY_DESC
    assert base.iaas_project_id == DUMMY_IAAS_ID


def test_project_create_inheritance():
    """Test ProjectCreate inherits from ProjectBase."""
    project = ProjectCreate(
        name=DUMMY_NAME, description=DUMMY_DESC, iaas_project_id=DUMMY_IAAS_ID
    )
    assert isinstance(project, ProjectBase)


def test_project_links_fields():
    """Test ProjectLinks field assignment and type."""
    url = "https://example.com/regions"
    links = ProjectLinks(regions=url)
    assert isinstance(links, ProjectLinks)
    assert links.regions == AnyHttpUrl(url)


def test_project_read_inheritance():
    """Test ProjectRead inheritance and adds links."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    links = ProjectLinks(regions="https://example.com/regions")
    project = ProjectRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        iaas_project_id=DUMMY_IAAS_ID,
        links=links,
    )
    assert isinstance(project, ItemID)
    assert isinstance(project, CreationRead)
    assert isinstance(project, EditableRead)
    assert isinstance(project, ProjectBase)
    assert project.links == links
    assert project.name == DUMMY_NAME
    assert project.description == DUMMY_DESC
    assert project.iaas_project_id == DUMMY_IAAS_ID


def test_project_list_structure():
    """Test ProjectList data field contains list of ProjectRead."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    links = ProjectLinks(regions="https://example.com/regions")
    project_read = ProjectRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        iaas_project_id=DUMMY_IAAS_ID,
        links=links,
    )
    project_list = ProjectList(
        data=[project_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url="https://api.com/projects",
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


def test_project_query_with_values():
    """Test ProjectQuery assigns provided values to its fields."""
    query = ProjectQuery(name=DUMMY_NAME, iaas_project_id=DUMMY_IAAS_ID)
    assert query.name == DUMMY_NAME
    assert query.iaas_project_id == DUMMY_IAAS_ID
