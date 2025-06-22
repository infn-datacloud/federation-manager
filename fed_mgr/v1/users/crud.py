"""User CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete users in the database.
It wraps generic CRUD operations with user-specific logic and exception handling.
"""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from fed_mgr.auth import AuthenticationDep
from fed_mgr.db import SessionDep
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

    """
    return add_item(session=session, entity=User, item=user)


def delete_user(*, session: Session, user_id: uuid.UUID) -> None:
    """Delete a user by their unique user_id from the database.

    Args:
        session: The database session.
        user_id: The UUID of the user to delete.

    """
    delete_item(session=session, entity=User, item_id=user_id)


def get_current_user(user_infos: AuthenticationDep, session: SessionDep) -> User | None:
    """Retrieve from the DB the user matching the user submitting the request.

    Args:
        user_infos: The authentication dependency containing user information.
        session: The database session dependency.

    Returns:
        User instance if found, otherwise None.

    """
    users, count = get_users(
        session=session,
        skip=0,
        limit=1,
        sort="-created_at",
        sub=user_infos.user_info["sub"],
        issuer=user_infos.user_info["iss"],
    )
    return None if count == 0 else users[0]


CurrenUserDep = Annotated[User, Depends(get_current_user)]
