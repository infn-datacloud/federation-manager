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

from pydantic import AnyHttpUrl

from fed_mgr.v1.identity_providers.user_groups.schemas import (
    UserGroup,
    UserGroupBase,
    UserGroupCreate,
    UserGroupLinks,
    UserGroupList,
    UserGroupQuery,
    UserGroupRead,
)


def test_user_group_base_fields():
    """Test UserGroupBase field assignment."""
    base = UserGroupBase(name="Test Group", description="desc")
    assert base.name == "Test Group"
    assert base.description == "desc"

def test_user_group_inheritance():
    """Test UserGroup inherits and assigns all fields."""
    id_ = uuid.uuid4()
    idp_id = uuid.uuid4()
    group = UserGroup(
        id=id_,
        created_at=1,
        created_by=id_,
        updated_at=2,
        updated_by=id_,
        name="Test Group",
        description="desc",
        idp=idp_id,
    )
    assert group.id == id_
    assert group.created_at == 1
    assert group.created_by == id_
    assert group.updated_at == 2
    assert group.updated_by == id_
    assert group.name == "Test Group"
    assert group.description == "desc"
    assert group.idp == idp_id

def test_user_group_create_is_base():
    """Test that UserGroupCreate is an instance of UserGroupBase."""
    group_create = UserGroupCreate(name="Test Group", description="desc")
    assert isinstance(group_create, UserGroupBase)

def test_user_group_links_fields():
    """Test UserGroupLinks field assignment."""
    url = AnyHttpUrl("https://api.com/slas")
    links = UserGroupLinks(slas=url)
    assert links.slas == url

def test_user_group_read_inheritance():
    """Test UserGroupRead inherits from UserGroup and adds links."""
    id_ = uuid.uuid4()
    idp_id = uuid.uuid4()
    url = AnyHttpUrl("https://api.com/slas")
    links = UserGroupLinks(slas=url)
    group_read = UserGroupRead(
        id=id_,
        created_at=1,
        created_by=id_,
        updated_at=2,
        updated_by=id_,
        name="Test Group",
        description="desc",
        idp=idp_id,
        links=links,
    )
    assert group_read.id == id_
    assert group_read.links == links

def test_user_group_list():
    """Test UserGroupList data field contains list of UserGroupRead."""
    id_ = uuid.uuid4()
    idp_id = uuid.uuid4()
    url = AnyHttpUrl("https://api.com/slas")
    links = UserGroupLinks(slas=url)
    group_read = UserGroupRead(
        id=id_,
        created_at=1,
        created_by=id_,
        updated_at=2,
        updated_by=id_,
        name="Test Group",
        description="desc",
        idp=idp_id,
        links=links,
    )
    group_list = UserGroupList(
        data=[group_read],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=AnyHttpUrl("https://api.com/groups"),
    )
    assert isinstance(group_list.data, list)
    assert group_list.data[0].id == id_

def test_user_group_query_defaults():
    """Test that UserGroupQuery initializes name to None by default."""
    query = UserGroupQuery()
    assert query.name is None

def test_user_group_query_with_values():
    """Test that UserGroupQuery assigns provided values to its fields."""
    query = UserGroupQuery(name="group")
    assert query.name == "group"
