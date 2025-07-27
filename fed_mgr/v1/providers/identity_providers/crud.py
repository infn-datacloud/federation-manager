"""Identity Provider CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete identity providers in
the database. It wraps generic CRUD operations with identity providers-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.v1.crud import (
    add_item,
    delete_item,
    get_item,
    get_items,
    update_item,
)
from fed_mgr.v1.models import IdentityProvider, IdpOverrides, Provider, User
from fed_mgr.v1.providers.identity_providers.schemas import IdpOverridesBase


def get_prov_idp_link(
    *, session: SessionDep, idp_id: uuid.UUID, provider_id: uuid.UUID
) -> IdpOverrides | None:
    """Retrieve the relationship between a resource provider and an identity provider.

    Use the resource provider and identity provider's unique IDs from the database.

    Args:
        session: The database session dependency.
        idp_id: The UUID of the identity provider to retrieve.
        provider_id: The UUID of the resource provider to retrieve.

    Returns:
        IdentityProvider instance if found, otherwise None.

    """
    return get_item(
        session=session,
        entity=IdpOverrides,
        idp_id=idp_id,
        provider_id=provider_id,
    )


def get_prov_idp_links(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[IdpOverrides], int]:
    """Retrieve a paginated and sorted list of IdP and providers relationships.

    The total count corresponds to the total count of returned values which may differs
    from the showed identity providers since they are paginated.

    Args:
        session: The database session.
        skip: Number of relationships to skip (for pagination).
        limit: Maximum number of relationships to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of IdpOverrides instances, total count of matching
        relationships).

    """
    return get_items(
        session=session,
        entity=IdpOverrides,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def connect_prov_idp(
    *,
    session: Session,
    overrides: IdpOverridesBase,
    created_by: User,
    idp: IdentityProvider,
    provider: Provider,
) -> IdpOverrides:
    """Connect an existing resource provider to an existing identity provider.

    Args:
        session: The database session.
        idp: The target Identity Provider's ID to link.
        provider: The target Resource Provider' ID to link.
        overrides: The IdP attributes to override for this specific connection.
        created_by: The User instance representing the creator of the identity provider.

    Returns:
        IdpOverrides: The relationship instance.

    """
    return add_item(
        session=session,
        entity=IdpOverrides,
        provider=provider,
        idp=idp,
        created_by=created_by,
        updated_by=created_by,
        **overrides.model_dump(),
    )


def update_prov_idp_link(
    *,
    session: Session,
    idp_id: uuid.UUID,
    provider_id: uuid.UUID,
    new_overrides: IdpOverridesBase,
    updated_by: User,
) -> None:
    """Update the data of a relationship between an identity provider and a provider.

    Completely override the relationship data.

    Args:
        session: The database session.
        idp_id: The UUID of the target identity provider.
        provider_id: The UUID of the target resource provider.
        new_overrides: The new data to update the identity provider with.
        updated_by: The User instance representing the updater of the identity provider.

    """
    return update_item(
        session=session,
        entity=IdpOverrides,
        idp_id=idp_id,
        provider_id=provider_id,
        updated_by=updated_by,
        **new_overrides.model_dump(),
    )


def disconnect_prov_idp(
    *, session: Session, idp_id: uuid.UUID, provider_id: uuid.UUID
) -> None:
    """Delete a identity provider by their unique idp_id from the database.

    Args:
        session: The database session.
        idp_id: The UUID of the relationship target identity provider.
        provider_id: The UUID of the relationship target resource provider.

    """
    delete_item(
        session=session,
        entity=IdpOverrides,
        idp_id=idp_id,
        provider_id=provider_id,
    )
