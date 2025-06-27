"""Resource Provider CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete resource providers in
the database. It wraps generic CRUD operations with resource providers-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.exceptions import ProviderStateChangeError, UserNotFoundError
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.models import Provider, User
from fed_mgr.v1.providers.schemas import ProviderCreate, ProviderStatus, ProviderUpdate
from fed_mgr.v1.schemas import ItemID
from fed_mgr.v1.users.crud import get_user

AVAILABLE_STATE_TRANSITIONS = {
    ProviderStatus.draft: [ProviderStatus.submitted],
    ProviderStatus.submitted: [ProviderStatus.ready, ProviderStatus.draft],
    ProviderStatus.ready: [ProviderStatus.evaluation, ProviderStatus.removed],
    ProviderStatus.evaluation: [ProviderStatus.pre_production, ProviderStatus.removed],
    ProviderStatus.pre_production: [
        ProviderStatus.active,
        ProviderStatus.evaluation,
        ProviderStatus.removed,
    ],
    ProviderStatus.active: [
        ProviderStatus.deprecated,
        ProviderStatus.degraded,
        ProviderStatus.maintenance,
    ],
    ProviderStatus.deprecated: [ProviderStatus.removed],
    ProviderStatus.removed: [],  # Final state
    ProviderStatus.degraded: [ProviderStatus.removed, ProviderStatus.maintenance],
    ProviderStatus.maintenance: [ProviderStatus.re_evaluation, ProviderStatus.removed],
    ProviderStatus.re_evaluation: [ProviderStatus.active, ProviderStatus.maintenance],
}


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

    At first, verify that given site administrators exist.

    Args:
        session: The database session.
        provider: The ProviderCreate model instance to add.
        created_by: The User instance representing the creator of the provider.

    Returns:
        ItemID: The identifier of the newly created provider.

    """
    site_admins = check_site_admins_exist(session=session, provider=provider)
    return add_item(
        session=session,
        entity=Provider,
        created_by=created_by.id,
        updated_by=created_by.id,
        site_admins=site_admins,
        **provider.model_dump(exclude={"site_admins"}),
    )


def update_provider(
    *,
    session: Session,
    provider_id: uuid.UUID,
    new_provider: ProviderUpdate,
    updated_by: User,
) -> None:
    """Update an provider by their unique provider_id from the database.

    Override only a subset of the provider entity attributes.

    Args:
        session: The database session.
        provider_id: The UUID of the provider to update.
        new_provider: The new data to update the provider with.
        updated_by: The User instance representing the updater of the provider.

    Returns:
        None

    """
    kwargs = {}
    site_admins = check_site_admins_exist(session=session, provider=new_provider)
    if len(site_admins) > 0:
        kwargs = {"site_admins": site_admins}
    return update_item(
        session=session,
        entity=Provider,
        item_id=provider_id,
        updated_by=updated_by.id,
        **new_provider.model_dump(exclude={"site_admins"}, esclude_none=True),
        **kwargs,
    )


def delete_provider(*, session: Session, provider_id: uuid.UUID) -> None:
    """Delete a provider by their unique provider_id from the database.

    Args:
        session: The database session.
        provider_id: The UUID of the provider to delete.

    Returns:
        None

    """
    delete_item(session=session, entity=Provider, item_id=provider_id)


def check_site_admins_exist(session: Session, provider: ProviderCreate) -> list[User]:
    """Check if all user IDs in the provider's site_admins list exist in the database.

    Args:
        session (Session): The database session used to query users.
        provider (ProviderCreate): The provider object containing a list of site admin
            user IDs.

    Returns:
        list: A list of user objects corresponding to the provided site admin user IDs.

    Raises:
        UserNotFoundError: If any user ID in provider.site_admins does not exist in the
            database.

    """
    site_admins = []
    for user_id in provider.site_admins:
        user = get_user(session=session, user_id=user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID '{user_id!s}' does not exist")
        site_admins.append(user)
    return site_admins


def change_provider_state(
    *,
    session: Session,
    provider_id: uuid.UUID,
    next_state: ProviderStatus,
    updated_by: User,
) -> None:
    """Update a provider changing only its state.

    Args:
        session: The database session.
        provider_id: The UUID of the provider to update.
        next_state: The target next provider state.
        updated_by: The User instance representing the updater of the provider.

    Returns:
        None

    Raises:
        ProviderStateChangeError: If the target state is not reachable from the current
            state.

    """
    db_provider = get_item(session=session, entity=Provider, item_id=provider_id)
    if (
        next_state != db_provider.status
        and next_state not in AVAILABLE_STATE_TRANSITIONS[db_provider.status]
    ):
        raise ProviderStateChangeError(
            f"Transition from state '{db_provider.status}' to state '{next_state}' is "
            "forbidden"
        )
    return update_item(
        session=session,
        entity=Provider,
        item_id=provider_id,
        updated_by=updated_by.id,
        status=next_state,
    )
