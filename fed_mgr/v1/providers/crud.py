"""Resource Provider CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete resource providers in
the database. It wraps generic CRUD operations with resource providers-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.models import Provider, User
from fed_mgr.v1.providers.schemas import ProviderCreate
from fed_mgr.v1.schemas import ItemID


def get_provider(*, session: SessionDep, provider_id: uuid.UUID) -> Provider | None:
    """Retrieve an provider by their unique provider_id from the database.

    Args:
        provider_id: The UUID of the provider to retrieve.
        session: The database session dependency.

    Returns:
        Provider instance if found, otherwise None.

    """
    return get_item(session=session, entity=Provider, item_id=provider_id)


def get_providers(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[Provider], int]:
    """Retrieve a paginated and sorted list of providers from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed providers since they are paginated.

    Args:
        session: The database session.
        skip: Number of providers to skip (for pagination).
        limit: Maximum number of providers to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of Provider instances, total count of matching providers).

    """
    return get_items(
        session=session,
        entity=Provider,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_provider(
    *, session: Session, provider: ProviderCreate, created_by: User
) -> ItemID:
    """Add a new provider to the database.

    Args:
        session: The database session.
        provider: The ProviderCreate model instance to add.
        created_by: The User instance representing the creator of the provider.

    Returns:
        ItemID: The identifier of the newly created provider.

    """
    return add_item(
        session=session,
        entity=Provider,
        item=provider,
        created_by=created_by.id,
        updated_by=created_by.id,
    )


def update_provider(
    *,
    session: Session,
    provider_id: uuid.UUID,
    new_provider: ProviderCreate,
    updated_by: User,
) -> None:
    """Update an provider by their unique provider_id from the database.

    Completely override an provider entity.

    Args:
        session: The database session.
        provider_id: The UUID of the provider to update.
        new_provider: The new data to update the provider with.
        updated_by: The User instance representing the updater of the provider.

    """
    return update_item(
        session=session,
        entity=Provider,
        item_id=provider_id,
        new_data=new_provider,
        updated_by=updated_by.id,
    )


def delete_provider(*, session: Session, provider_id: uuid.UUID) -> None:
    """Delete a provider by their unique provider_id from the database.

    Args:
        session: The database session.
        provider_id: The UUID of the provider to delete.

    """
    delete_item(session=session, entity=Provider, item_id=provider_id)
