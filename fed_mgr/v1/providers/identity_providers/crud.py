"""Identity Provider CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete identity providers in
the database. It wraps generic CRUD operations with identity providers-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.identity_providers.crud import get_idp
from fed_mgr.v1.models import IdpOverrides, Provider, User
from fed_mgr.v1.providers.identity_providers.schemas import (
    IdpOverridesBase,
    ProviderIdPConnectionCreate,
)


def get_idp_overrides(
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


def get_idp_overrides_list(
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
    config: ProviderIdPConnectionCreate,
    created_by: User,
    provider: Provider,
) -> IdpOverrides:
    """Connect an existing resource provider to an existing identity provider.

    Args:
        session: The database session.
        provider: The target Resource Provider' ID to link.
        config: The IdP attributes to override for this specific connection.
        created_by: The User instance representing the creator of the identity provider.

    Returns:
        IdpOverrides: The relationship instance.

    """
    idp = get_idp(session=session, idp_id=config.idp_id)
    if idp is None:
        raise ItemNotFoundError(
            f"Identity provider with ID '{config.idp_id!s}' does not exist"
        )
    return add_item(
        session=session,
        entity=IdpOverrides,
        provider=provider,
        idp=idp,
        created_by=created_by,
        updated_by=created_by,
        **config.overrides.model_dump(),
    )


def update_idp_overrides(
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
    return delete_item(
        session=session,
        entity=IdpOverrides,
        idp_id=idp_id,
        provider_id=provider_id,
    )
