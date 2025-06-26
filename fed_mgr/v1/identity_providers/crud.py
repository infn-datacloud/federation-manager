"""Identity Provider CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete identity providers in
the database. It wraps generic CRUD operations with identity providers-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.v1.models import IdentityProvider, User
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.identity_providers.schemas import IdentityProviderCreate
from fed_mgr.v1.schemas import ItemID


def get_idp(*, session: SessionDep, idp_id: uuid.UUID) -> IdentityProvider | None:
    """Retrieve an identity provider by their unique idp_id from the database.

    Args:
        idp_id: The UUID of the identity provider to retrieve.
        session: The database session dependency.

    Returns:
        IdentityProvider instance if found, otherwise None.

    """
    return get_item(session=session, entity=IdentityProvider, item_id=idp_id)


def get_idps(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[IdentityProvider], int]:
    """Retrieve a paginated and sorted list of identity providers from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed identity providers since they are paginated.

    Args:
        session: The database session.
        skip: Number of identity providers to skip (for pagination).
        limit: Maximum number of identity providers to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of IdentityProvider instances, total count of matching identity
        providers).

    """
    return get_items(
        session=session,
        entity=IdentityProvider,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_idp(
    *, session: Session, idp: IdentityProviderCreate, created_by: User
) -> ItemID:
    """Add a new identity provider to the database.

    Args:
        session: The database session.
        idp: The IdentityProviderCreate model instance to add.
        created_by: The User instance representing the creator of the identity provider.

    Returns:
        ItemID: The identifier of the newly created identity provider.

    """
    return add_item(
        session=session,
        entity=IdentityProvider,
        item=idp,
        created_by=created_by.id,
        updated_by=created_by.id,
    )


def update_idp(
    *,
    session: Session,
    idp_id: uuid.UUID,
    new_idp: IdentityProviderCreate,
    updated_by: User,
) -> None:
    """Update an identity provider by their unique idp_id from the database.

    Completely override an idp entity.

    Args:
        session: The database session.
        idp_id: The UUID of the identity provider to update.
        new_idp: The new data to update the identity provider with.
        updated_by: The User instance representing the updater of the identity provider.

    """
    return update_item(
        session=session,
        entity=IdentityProvider,
        item_id=idp_id,
        new_data=new_idp,
        updated_by=updated_by.id,
    )


def delete_idp(*, session: Session, idp_id: uuid.UUID) -> None:
    """Delete a identity provider by their unique idp_id from the database.

    Args:
        session: The database session.
        idp_id: The UUID of the identity provider to delete.

    """
    delete_item(session=session, entity=IdentityProvider, item_id=idp_id)
