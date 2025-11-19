"""User CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete users in the database.
It wraps generic CRUD operations with user-specific logic and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.auth import (
    FAKE_USER_EMAIL,
    FAKE_USER_ISSUER,
    FAKE_USER_NAME,
    FAKE_USER_SUBJECT,
)
from fed_mgr.db import SessionDep
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.models import User
from fed_mgr.v1.users.schemas import UserCreate


def get_user(*, session: SessionDep, user_id: uuid.UUID) -> User | None:
    """Retrieve a user by their unique user_id from the database.

    Args:
        session: The database session dependency.
        user_id: The UUID of the user to retrieve. If present, kwargs is ignored.

    Returns:
        User instance if found, otherwise None.

    """
    return get_item(session=session, entity=User, id=user_id)


def get_users(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[User], int]:
    """Retrieve a paginated and sorted list of users from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed users since they are paginated.

    Args:
        session: The database session.
        skip: Number of users to skip (for pagination).
        limit: Maximum number of users to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of User instances, total count of matching users).

    """
    return get_items(
        session=session, entity=User, skip=skip, limit=limit, sort=sort, **kwargs
    )


def add_user(*, session: Session, user: UserCreate) -> User:
    """Add a new user to the database.

    Args:
        session: The database session.
        user: The UserCreate model instance to add.

    Returns:
        User: The identifier of the newly created user.

    """
    return add_item(session=session, entity=User, **user.model_dump())


def update_user(*, session: Session, user_id: uuid.UUID, new_user: UserCreate) -> None:
    """Update a user by their unique user_id from the database.

    Completely override a user entity.

    Args:
        session: The database session.
        user_id: The UUID of the user to delete.
        new_user: The new data to update the user with.

    """
    return update_item(
        session=session, entity=User, id=user_id, **new_user.model_dump()
    )


def delete_user(*, session: Session, user_id: uuid.UUID) -> None:
    """Delete a user by their unique user_id from the database.

    Args:
        session: The database session.
        user_id: The UUID of the user to delete.

    """
    return delete_item(session=session, entity=User, id=user_id)


def create_fake_user(session: Session) -> User:
    """Create a fake user in the database for testing or development purposes.

    If the fake user already exists return the ID of the existing user.

    Args:
        session: An active SQLModel session for database operations.

    Returns:
        the id of the fake user.

    """
    _, tot_items = get_users(
        session=session,
        skip=0,
        limit=1,
        sort="-created_at",
        name=FAKE_USER_NAME,
        issuer=FAKE_USER_ISSUER,
    )
    if tot_items == 0:
        return add_user(
            session=session,
            user=UserCreate(
                name=FAKE_USER_NAME,
                email=FAKE_USER_EMAIL,
                sub=FAKE_USER_SUBJECT,
                issuer=FAKE_USER_ISSUER,
            ),
        )


def delete_fake_user(session: Session) -> None:
    """Delete the fake user in the database used for testing or development purposes.

    Args:
        session: An active SQLModel session for database operations.
        user_id: ID of the user to delete.

    """
    users, tot_items = get_users(
        session=session,
        skip=0,
        limit=1,
        sort="-created_at",
        name=FAKE_USER_NAME,
        issuer=FAKE_USER_ISSUER,
    )
    if tot_items > 0:
        return delete_user(session=session, user_id=users[0].id)
