"""User CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete users in the database.
It wraps generic CRUD operations with user-specific logic and exception handling.
"""

import uuid

import sqlalchemy
from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.exceptions import ConflictError
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items
from fed_mgr.v1.schemas import ItemID
from fed_mgr.v1.users.schemas import User, UserCreate


def get_user(user_id: uuid.UUID, session: SessionDep) -> User | None:
    """Retrieve a user by their unique user_id from the database.

    Args:
        user_id: The UUID of the user to retrieve.
        session: The database session dependency.

    Returns:
        User instance if found, otherwise None.

    """
    return get_item(session=session, entity=User, item_id=user_id)


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


def add_user(*, session: Session, user: UserCreate) -> ItemID:
    """Add a new user to the database.

    Args:
        session: The database session.
        user: The UserCreate model instance to add.

    Returns:
        ItemID: The identifier of the newly created user.

    Raises:
        ConflictError: If a user with the same sub and issuer already exists.

    """
    try:
        return add_item(session=session, entity=User, item=user)
    except sqlalchemy.exc.IntegrityError as e:
        if "UNIQUE constraint failed: user.sub, user.issuer" in e.args[0]:
            raise ConflictError(
                f"User with sub '{user.sub}' and belonging to issuer "
                f"'{user.issuer}' already exists"
            ) from e


def delete_user(*, session: Session, user_id: uuid.UUID) -> None:
    """Delete a user by their unique user_id from the database.

    Args:
        session: The database session.
        user_id: The UUID of the user to delete.

    """
    delete_item(session=session, entity=User, item_id=user_id)
