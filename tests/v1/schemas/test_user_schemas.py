"""Unit tests for the user Pydantic schemas in fed_mgr.v1.users.schemas module.

This test suite covers:
- Validation of the UserBase schema, including correct and incorrect email and issuer
  values.
- Inheritance and field presence in the User model, including the created_at timestamp.
- UserCreate schema validation and its inheritance from UserBase.
- Default values and value assignment in the UserQuery schema.
- Construction and field validation of the UserList schema, including correct
  aggregation of User instances.

Tested Schemas:
- UserBase: Basic user information with validation for email and issuer fields.
- User: Extends UserBase with additional fields such as id and created_at.
- UserCreate: Used for user creation, inherits from UserBase.
- UserQuery: Used for querying users, supports optional filtering fields.
- UserList: Represents a paginated list of users.

Fixtures and dummy values are used to ensure consistent and isolated test cases.
"""

import uuid
from datetime import datetime

import pytest
from pydantic import AnyHttpUrl, ValidationError

from fed_mgr.v1.schemas import CreationTimeRead, ItemID
from fed_mgr.v1.users.schemas import (
    UserBase,
    UserCreate,
    UserList,
    UserQuery,
    UserRead,
)

DUMMY_SUB = "user-123"
DUMMY_NAME = "John Doe"
DUMMY_EMAIL = "john.doe@example.com"
DUMMY_ISSUER = "https://issuer.example.com"
DUMMY_ENDPOINT = "https://example.com"


def test_user_base_fields():
    """Test that UserBase is created successfully with valid dummy values.

    Asserts that all fields are set correctly.
    """
    user = UserBase(
        sub=DUMMY_SUB, name=DUMMY_NAME, email=DUMMY_EMAIL, issuer=DUMMY_ISSUER
    )
    assert user.sub == DUMMY_SUB
    assert user.name == DUMMY_NAME
    assert user.email == DUMMY_EMAIL
    assert isinstance(user.issuer, AnyHttpUrl)
    assert user.issuer == AnyHttpUrl(DUMMY_ISSUER)


@pytest.mark.parametrize("email", ["not-an-email", "missingatsign.com", "user@.com"])
def test_user_base_invalid_email(email):
    """Test that UserBase raises ValidationError for invalid email values."""
    with pytest.raises(ValidationError):
        UserBase(sub=DUMMY_SUB, name=DUMMY_NAME, email=email, issuer=DUMMY_ISSUER)


@pytest.mark.parametrize(
    "issuer",
    ["not-a-url", "ftp://nothttp.com"],  # "http:/broken.com" does not raise error
)
def test_user_base_invalid_issuer(issuer):
    """Test that UserBase raises ValidationError for invalid issuer values."""
    with pytest.raises(ValidationError):
        UserBase(sub=DUMMY_SUB, name=DUMMY_NAME, email=DUMMY_EMAIL, issuer=issuer)


def test_user_create_is_user_base():
    """Test that UserCreate is an instance of UserBase."""
    user_create = UserCreate(
        sub=DUMMY_SUB,
        name=DUMMY_NAME,
        email=DUMMY_EMAIL,
        issuer=DUMMY_ISSUER,
    )
    assert isinstance(user_create, UserBase)


def test_user_read_inheritance():
    """Test SLARead inherits from SLA and adds links."""
    id_ = uuid.uuid4()
    now = datetime.now()
    sla_read = UserRead(
        id=id_,
        created_at=now,
        sub=DUMMY_SUB,
        name=DUMMY_NAME,
        email=DUMMY_EMAIL,
        issuer=DUMMY_ISSUER,
    )
    assert isinstance(sla_read, ItemID)
    assert isinstance(sla_read, CreationTimeRead)
    assert isinstance(sla_read, UserBase)


def test_user_list_data_field():
    """Test UserList data field contains list of User."""
    id_ = uuid.uuid4()
    now = datetime.now()
    user = UserRead(
        id=id_,
        created_at=now,
        sub=DUMMY_SUB,
        name=DUMMY_NAME,
        email=DUMMY_EMAIL,
        issuer=DUMMY_ISSUER,
    )
    user_list = UserList(
        data=[user],
        page_number=1,
        page_size=1,
        tot_items=1,
        resource_url=DUMMY_ENDPOINT,
    )
    assert isinstance(user_list.data, list)
    assert user_list.data[0].sub == DUMMY_SUB


def test_user_query_defaults():
    """Test that UserQuery initializes all fields to None by default."""
    query = UserQuery()
    assert query.sub is None
    assert query.name is None
    assert query.email is None
    assert query.issuer is None


def test_user_query_with_values():
    """Test that UserQuery assigns provided values to its fields."""
    query = UserQuery(
        sub="abc",
        name="doe",
        email="john",
        issuer="issuer",
    )
    assert query.sub == "abc"
    assert query.name == "doe"
    assert query.email == "john"
    assert query.issuer == "issuer"
