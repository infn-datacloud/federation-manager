"""Resource Provider CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete resource providers in
the database. It wraps generic CRUD operations with resource providers-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.exceptions import ItemNotFoundError, ProviderStateChangeError
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.models import Provider, User
from fed_mgr.v1.providers.schemas import ProviderCreate, ProviderStatus, ProviderUpdate
from fed_mgr.v1.users.crud import get_user

AVAILABLE_STATE_TRANSITIONS = {
    ProviderStatus.draft: [ProviderStatus.ready],
    ProviderStatus.ready: [ProviderStatus.submitted, ProviderStatus.draft],
    ProviderStatus.submitted: [ProviderStatus.evaluation, ProviderStatus.removed],
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
    return get_item(session=session, entity=Provider, id=provider_id)


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
) -> Provider:
    """Add a new provider to the database.

    At first, verify that given site administrators exist.

    Args:
        session: The database session.
        provider: The ProviderCreate model instance to add.
        created_by: The User instance representing the creator of the provider.

    Returns:
        Provider: The identifier of the newly created provider.

    """
    site_admins = check_users_exist(session=session, user_ids=provider.site_admins)
    return add_item(
        session=session,
        entity=Provider,
        created_by=created_by,
        updated_by=created_by,
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
    if new_provider.site_admins is not None:
        site_admins = check_users_exist(
            session=session, user_ids=new_provider.site_admins
        )
        kwargs = {"site_admins": site_admins}
    return update_item(
        session=session,
        entity=Provider,
        id=provider_id,
        updated_by=updated_by,
        **new_provider.model_dump(exclude_none=True),
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
    delete_item(session=session, entity=Provider, id=provider_id)


def check_users_exist(session: Session, user_ids: list[uuid.UUID]) -> list[User]:
    """Check if all user IDs in the provider's site_admins list exist in the database.

    Args:
        session (Session): The database session used to query users.
        user_ids (ProviderCreate): The provider object containing a list of site
            admin user IDs.

    Returns:
        list: A list of user objects corresponding to the provided site admin user IDs.

    Raises:
        ItemNotFoundError: If any user ID in provider.site_admins does not exist in the
            database.

    """
    users = []
    for user_id in user_ids:
        user = get_user(session=session, user_id=user_id)
        if user is None:
            raise ItemNotFoundError("User", id=user_id)
        users.append(user)
    return users


def add_site_tester(*, session: Session, provider: Provider, user: User) -> None:
    """Add a user to the list of site testers for a given provider.

    Args:
        session (Session): The SQLAlchemy session used to interact with the database.
        provider (Provider): The provider object whose site testers list will be
            updated.
        user (User): The user to be added as a site tester.

    Returns:
        None

    Raises:
        Any exceptions raised by the session commit will propagate.

    """
    new_site_testers = set(provider.site_testers)
    new_site_testers = new_site_testers.add(user)
    provider.site_testers = list(new_site_testers)
    session.add(provider)
    session.commit()


def remove_site_tester(*, session: Session, provider: Provider, user: User) -> None:
    """Remove a specified user from the list of site testers associated with a provider.

    Args:
        session (Session): The database session used to commit changes.
        provider (Provider): The provider object from which the site tester will be
            removed.
        user (User): The user to be removed from the provider's site testers.

    Returns:
        None

    Raises:
        IndexError: If the user is not found in the provider's site testers list.

    """
    i = 0
    for site_tester in provider.site_testers:
        if user.id == site_tester.id:
            break
        i += 1
    provider.site_testers.pop(i)
    session.add(provider)
    session.commit()


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
    db_provider = get_item(session=session, entity=Provider, id=provider_id)
    if (
        next_state != db_provider.status
        and next_state not in AVAILABLE_STATE_TRANSITIONS[db_provider.status]
    ):
        raise ProviderStateChangeError(db_provider.status, next_state)
    return update_item(
        session=session,
        entity=Provider,
        id=provider_id,
        updated_by=updated_by,
        status=next_state,
    )
