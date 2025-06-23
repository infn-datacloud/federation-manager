"""User Group CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete user groups in
the database. It wraps generic CRUD operations with user groups-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.identity_providers.schemas import IdentityProvider
from fed_mgr.v1.identity_providers.user_groups.schemas import (
    UserGroup,
    UserGroupCreate,
)
from fed_mgr.v1.schemas import ItemID
from fed_mgr.v1.users.schemas import User


def get_user_group(user_group_id: uuid.UUID, session: SessionDep) -> UserGroup | None:
    """Retrieve an user group by their unique user_group_id from the database.

    Args:
        user_group_id: The UUID of the user group to retrieve.
        session: The database session dependency.

    Returns:
        UserGroup instance if found, otherwise None.

    """
    return get_item(session=session, entity=UserGroup, item_id=user_group_id)


def get_user_groups(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[UserGroup], int]:
    """Retrieve a paginated and sorted list of user groups from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed user groups since they are paginated.

    Args:
        session: The database session.
        skip: Number of user groups to skip (for pagination).
        limit: Maximum number of user groups to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of UserGroup instances, total count of matching identity
        providers).

    """
    return get_items(
        session=session,
        entity=UserGroup,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_user_group(
    *,
    session: Session,
    user_group: UserGroupCreate,
    created_by: User,
    parent_idp: IdentityProvider,
) -> ItemID:
    """Add a new user group to the database.

    Args:
        session: The database session.
        user_group: The UserGroupCreate model instance to add.
        created_by: The User istance representing the creator of the identity provider.
        parent_idp: The user group's parent identity provider.

    Returns:
        ItemID: The identifier of the newly created user group.

    """
    return add_item(
        session=session,
        entity=UserGroup,
        item=user_group,
        created_by=created_by.id,
        updated_by=created_by.id,
        idp=parent_idp.id,
    )


def update_user_group(
    *,
    session: Session,
    user_group_id: uuid.UUID,
    new_user_group: UserGroupCreate,
    updated_by: User,
) -> None:
    """Update an user group by their unique user_group_id from the database.

    Completely override an user_group entity.

    Args:
        session: The database session.
        user_group_id: The UUID of the user group to update.
        new_user_group: The new data to update the user group with.
        updated_by: The User instance representing the updater of the user group.

    """
    return update_item(
        session=session,
        entity=UserGroup,
        item_id=user_group_id,
        new_data=new_user_group,
        updated_by=updated_by.id,
    )


def delete_user_group(*, session: Session, user_group_id: uuid.UUID) -> None:
    """Delete a user group by their unique user_group_id from the database.

    Args:
        session: The database session.
        user_group_id: The UUID of the user group to delete.

    """
    delete_item(session=session, entity=UserGroup, item_id=user_group_id)
