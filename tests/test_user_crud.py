"""Unit tests for CRUD operations related to the User entity in the fe-mgr app.

This module contains tests for the following functionalities:
- Retrieving a user by ID (`get_user`)
- Retrieving multiple users with pagination and sorting (`get_users`)
- Adding a new user (`add_user`)
- Handling unique constraint violations when adding a user
- Deleting a user by ID (`delete_user`)

Fixtures:
    session: Provides a mock database session for testing.
    user_id: Generates a unique UUID for user identification in tests.

Test Cases:
    test_get_user_found: Verifies that `get_user` returns the expected user object
        when found.
    test_get_user_not_found: Verifies that `get_user` returns None when the user is
        not found.
    test_get_users_returns_users_and_count: Verifies that `get_users` returns a tuple
        of users and total count.
    test_get_users_returns_empty_list_and_zero_count: Verifies that `get_users`
        returns an empty list and zero count when no users are found.
    test_add_user_success: Verifies that `add_user` successfully adds a user and
        returns the result.
    test_add_user_conflict_error: Verifies that `add_user` raises a ConflictError on
        unique constraint violation.
    test_delete_user_calls_delete_item: Verifies that `delete_user` calls the delete
        operation with correct arguments.
"""

import uuid
from unittest import mock

import pytest
import sqlalchemy

from fed_mgr.exceptions import ConflictError
from fed_mgr.v1.users.crud import add_user, delete_user, get_user, get_users
from fed_mgr.v1.users.schemas import User, UserCreate


@pytest.fixture
def user_id():
    """Generate and return a new unique user ID using UUID version 4.

    Returns:
        uuid.UUID: A randomly generated UUID object representing a unique user ID.

    """
    return uuid.uuid4()


def test_get_user_found(session, user_id):
    """Test that the `get_user` returns the expected user object when the user is found.

    Args:
        session: The database session used for querying.
        user_id: The ID of the user to retrieve.

    Behavior:
        - Mocks the `get_item` function to return a fake user object.
        - Asserts that `get_item` is called once with the correct parameters.
        - Asserts that the result of `get_user` is the mocked user object.

    """
    fake_user = mock.Mock(spec=User)
    with mock.patch(
        "fed_mgr.v1.users.crud.get_item", return_value=fake_user
    ) as mock_get_item:
        result = get_user(user_id, session)
        mock_get_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id
        )
        assert result is fake_user


def test_get_user_not_found(session, user_id):
    """Test that `get_user` returns None when the user with the given id is not found.

    This test mocks the `get_item` function to return None, simulating the case where
    the requested user does not exist in the database. It then asserts that `get_user`
    returns None and that `get_item` was called once with the correct arguments.

    Args:
        session: The database session used for the query.
        user_id: The ID of the user to retrieve.

    """
    with mock.patch(
        "fed_mgr.v1.users.crud.get_item", return_value=None
    ) as mock_get_item:
        result = get_user(user_id, session)
        mock_get_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id
        )
        assert result is None


def test_get_users_returns_users_and_count(session):
    """Verify that `get_users` returns a tuple with a list of user and total count.

    This test mocks the `get_items` function to return a fake list of users and a
    count, then asserts that `get_users` returns the expected tuple and that
    `get_items` is called with the correct arguments.

    Args:
        session: The mock database session used for the query.

    """
    fake_users = [mock.Mock(spec=User), mock.Mock(spec=User)]
    fake_count = 2
    with mock.patch(
        "fed_mgr.v1.users.crud.get_items", return_value=(fake_users, fake_count)
    ) as mock_get_items:
        result = get_users(session=session, skip=0, limit=10, sort="id")
        mock_get_items.assert_called_once_with(
            session=session, entity=User, skip=0, limit=10, sort="id"
        )
        assert result == (fake_users, fake_count)


def test_get_users_returns_empty_list_and_zero_count(session):
    """Verify that `get_users` returns an empty list and zero count when no users.

    This test mocks the `get_items` function to return an empty list and zero count,
    then asserts that `get_users` returns the expected tuple and that `get_items` is
    called with the correct arguments.

    Args:
        session: The mock database session used for the query.

    """
    fake_users = []
    fake_count = 0
    with mock.patch(
        "fed_mgr.v1.users.crud.get_items", return_value=(fake_users, fake_count)
    ) as mock_get_items:
        result = get_users(session=session, skip=0, limit=10, sort="id")
        mock_get_items.assert_called_once_with(
            session=session, entity=User, skip=0, limit=10, sort="id"
        )
        assert result == (fake_users, fake_count)


def test_add_user_success(session):
    """Verify that `add_user` calls `add_item`.

    This test mocks the `add_item` function to return a fake user object, then
    asserts that `add_user` returns the expected result and that `add_item` is
    called once with the correct arguments.

    Args:
        session: The mock database session used for the operation.

    """
    fake_user_create = mock.Mock(spec=UserCreate)
    fake_item_id = mock.Mock()
    with mock.patch(
        "fed_mgr.v1.users.crud.add_item", return_value=fake_item_id
    ) as mock_add_item:
        result = add_user(session=session, user=fake_user_create)
        mock_add_item.assert_called_once_with(
            session=session, entity=User, item=fake_user_create
        )
        assert result is fake_item_id


def test_add_user_conflict_error(session):
    """Verify that `add_user` raises a `ConflictError` on unique constraint violation.

    This test mocks the `add_item` function to raise an `IntegrityError` simulating
    a unique constraint violation, then asserts that `add_user` raises a
    `ConflictError` and the error message contains 'already exists'.

    Args:
        session: The mock database session used for the operation.

    """
    fake_user_create = mock.Mock(spec=UserCreate)
    # Add required attribute to avoid AttributeError
    fake_user_create.sub = "fake-sub"
    fake_user_create.issuer = "fake-issuer"
    # Simulate IntegrityError with unique constraint message
    exc = sqlalchemy.exc.IntegrityError(
        statement=None,
        params=None,
        orig=Exception("UNIQUE constraint failed: user.sub, user.issuer"),
    )
    exc.args = ("UNIQUE constraint failed: user.sub, user.issuer",)
    with mock.patch("fed_mgr.v1.users.crud.add_item", side_effect=exc):
        with pytest.raises(ConflictError) as e:
            add_user(session=session, user=fake_user_create)
        assert "already exists" in str(e.value)


def test_delete_user_calls_delete_item(session, user_id):
    """Verify that `delete_user` calls `delete_item` with the correct arguments.

    This test mocks the `delete_item` function and asserts that it is called once
    with the correct session, entity, and user_id arguments when `delete_user` is
    invoked.

    Args:
        session: The mock database session used for the operation.
        user_id: The ID of the user to delete.

    """
    with mock.patch("fed_mgr.v1.users.crud.delete_item") as mock_delete_item:
        delete_user(session=session, user_id=user_id)
        mock_delete_item.assert_called_once_with(
            session=session, entity=User, item_id=user_id
        )
