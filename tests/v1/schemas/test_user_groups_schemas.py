"""Unit tests for fed_mgr.v1.identity_providers.user_groups.schemas.

Tests in this file:
- test_user_group_base_fields
- test_user_group_inheritance
- test_user_group_create_is_base
- test_user_group_links_fields
- test_user_group_read_inheritance
- test_user_group_list
- test_user_group_query_defaults
- test_user_group_query_with_values
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

from pydantic import AnyHttpUrl

from fed_mgr.v1 import SLAS_PREFIX
from fed_mgr.v1.identity_providers.user_groups.schemas import (
    UserGroupBase,
    UserGroupCreate,
    UserGroupLinks,
    UserGroupList,
    UserGroupQuery,
    UserGroupRead,
)
from fed_mgr.v1.schemas import (
    CreationQuery,
    CreationRead,
    DescriptionQuery,
    EditableQuery,
    EditableRead,
    ItemDescription,
    ItemID,
    PaginationQuery,
    SortQuery,
)

DUMMY_DESC = "desc"
DUMMY_NAME = "Test Group"
DUMMY_ENDPOINT = "https://example.com"


def test_user_group_base_fields():
    """Test UserGroupBase field assignment."""
    base = UserGroupBase(name=DUMMY_NAME, description=DUMMY_DESC)
    assert isinstance(base, ItemDescription)
    assert base.name == DUMMY_NAME


def test_user_group_create_is_base():
    """Test that UserGroupCreate is an instance of UserGroupBase."""
    group_create = UserGroupCreate(name=DUMMY_NAME, description=DUMMY_DESC)
    assert isinstance(group_create, UserGroupBase)


def test_user_group_links_fields():
    """Test UserGroupLinks field assignment."""
    links = UserGroupLinks(slas=DUMMY_ENDPOINT)
    assert links.slas == AnyHttpUrl(DUMMY_ENDPOINT)


def test_user_group_read_inheritance():
    """Test UserGroupRead inherits from UserGroup and adds links."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    group_read = UserGroupRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        base_url=DUMMY_ENDPOINT,
    )
    assert isinstance(group_read, ItemID)
    assert isinstance(group_read, CreationRead)
    assert isinstance(group_read, EditableRead)
    assert isinstance(group_read, UserGroupBase)
    assert isinstance(group_read.links, UserGroupLinks)
    assert group_read.links.slas == AnyHttpUrl(f"{DUMMY_ENDPOINT}/{id_}{SLAS_PREFIX}")


def test_user_group_list():
    """Test UserGroupList data field contains list of UserGroupRead."""
    creator = uuid.uuid4()
    id_ = uuid.uuid4()
    now = datetime.now()
    idp = MagicMock()
    group_read = UserGroupRead(
        id=id_,
        created_at=now,
        created_by=creator,
        updated_at=now,
        updated_by=creator,
        name=DUMMY_NAME,
        description=DUMMY_DESC,
        idp=idp,
        base_url=DUMMY_ENDPOINT,
    )
    group_list = UserGroupList(
        data=[group_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=DUMMY_ENDPOINT,
    )
    assert isinstance(group_list.data, list)
    assert group_list.data[0] == group_read


def test_user_group_query_defaults():
    """Test that UserGroupQuery initializes name to None by default."""
    query = UserGroupQuery()
    assert isinstance(query, DescriptionQuery)
    assert isinstance(query, CreationQuery)
    assert isinstance(query, EditableQuery)
    assert isinstance(query, SortQuery)
    assert isinstance(query, PaginationQuery)
    assert query.name is None


def test_user_group_query_with_values():
    """Test that UserGroupQuery assigns provided values to its fields."""
    query = UserGroupQuery(name="group")
    assert query.name == "group"
