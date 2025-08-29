"""Resource Provider CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete resource providers in
the database. It wraps generic CRUD operations with resource providers-specific logic
and exception handling.
"""

import uuid

from sqlalchemy import event
from sqlmodel import Session

from fed_mgr.config import get_settings
from fed_mgr.db import SessionDep
from fed_mgr.exceptions import ItemNotFoundError, ProviderStateChangeError
from fed_mgr.kafka import send_provider_to_be_evaluated
from fed_mgr.logger import get_logger
from fed_mgr.utils import check_list_not_empty
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
    return update_item(
        session=session,
        entity=Provider,
        id=provider_id,
        updated_by=updated_by,
        **new_provider.model_dump(exclude_none=True),
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


def add_site_testers(
    *, session: Session, provider: Provider, user_ids: list[uuid.UUID], updated_by: User
) -> None:
    """Add a user to the list of site testers for a given provider.

    Args:
        session (Session): The SQLAlchemy session used to interact with the database.
        provider (Provider): The provider object whose site testers list will be
            updated.
        user_ids (User): The user to be added as a site tester.
        updated_by: User who made operation

    Returns:
        None

    Raises:
        Any exceptions raised by the session commit will propagate.

    """
    users = check_users_exist(session=session, user_ids=user_ids)
    provider.site_testers = list(set(provider.site_testers) | set(users))
    provider.updated_by = updated_by
    session.add(provider)
    session.commit()


def add_site_admins(
    *, session: Session, provider: Provider, user_ids: list[uuid.UUID], updated_by: User
) -> None:
    """Add a user to the list of site testers for a given provider.

    Args:
        session (Session): The SQLAlchemy session used to interact with the database.
        provider (Provider): The provider object whose site testers list will be
            updated.
        user_ids (User): The user to be added as a site tester.
        updated_by: User who made operation

    Returns:
        None

    Raises:
        Any exceptions raised by the session commit will propagate.

    """
    users = check_users_exist(session=session, user_ids=user_ids)
    provider.site_admins = list(set(provider.site_admins) | set(users))
    provider.updated_by = updated_by
    session.add(provider)
    session.commit()


def remove_site_testers(
    *, session: Session, provider: Provider, user_ids: list[uuid.UUID], updated_by: User
) -> None:
    """Remove a specified user from the list of site testers associated with a provider.

    Args:
        session (Session): The database session used to commit changes.
        provider (Provider): The provider object from which the site tester will be
            removed.
        user_ids (User): The user to be removed from the provider's site testers.
        updated_by: User who made operation

    Returns:
        None

    Raises:
        IndexError: If the user is not found in the provider's site testers list.

    """
    users = check_users_exist(session=session, user_ids=user_ids)
    provider.site_testers = list(set(provider.site_testers) - set(users))
    provider.updated_by = updated_by
    session.add(provider)
    session.commit()


def remove_site_admins(
    *, session: Session, provider: Provider, user_ids: list[uuid.UUID], updated_by: User
) -> None:
    """Remove a specified user from the list of site testers associated with a provider.

    Args:
        session (Session): The database session used to commit changes.
        provider (Provider): The provider object from which the site tester will be
            removed.
        user_ids (User): The user to be removed from the provider's site testers.
        updated_by: User who made operation

    Returns:
        None

    Raises:
        IndexError: If the user is not found in the provider's site testers list.

    """
    users = check_users_exist(session=session, user_ids=user_ids)
    new_admins = list(set(provider.site_admins) - set(users))
    provider.site_admins = check_list_not_empty(new_admins)
    provider.updated_by = updated_by
    session.add(provider)
    session.commit()


def change_provider_state(
    *,
    session: Session,
    provider: Provider,
    next_state: ProviderStatus,
    updated_by: User,
) -> None:
    """Force Update a provider changing only its state.

    Args:
        session: The database session.
        provider: The UUID of the provider to update.
        next_state: The target next provider state.
        updated_by: The User instance representing the updater of the provider.

    Returns:
        None

    Raises:
        ProviderStateChangeError: If the target state is not reachable from the current
            state.

    """
    provider.status = next_state
    provider.updated_by = updated_by
    session.add(provider)
    session.commit()


def submit_provider(*, session: Session, provider: Provider, updated_by: User) -> None:
    """Submit a provider for further processing by updating its status.

    Args:
        session (Session): The database session used to commit changes.
        provider (Provider): The provider instance to be submitted.
        updated_by (User): The user performing the submission.

    Raises:
        ProviderStateChangeError: If the provider's current status is not 'ready'.

    Returns:
        None

    """
    if provider.status != ProviderStatus.ready:
        raise ProviderStateChangeError(provider.status, ProviderStatus.submitted)
    provider.status = ProviderStatus.submitted
    provider.updated_by = updated_by
    session.add(provider)
    session.commit()


def unsubmit_provider(
    *, session: Session, provider: Provider, updated_by: User
) -> None:
    """Revert a provider's status from 'submitted' to 'ready'.

    Args:
        session (Session): The database session to use for committing changes.
        provider (Provider): The provider instance whose status will be updated.
        updated_by (User): The user performing the update.

    Raises:
        ProviderStateChangeError: If the provider's current status is not 'submitted'.

    Retruns:
        None

    """
    if provider.status != ProviderStatus.submitted:
        raise ProviderStateChangeError(provider.status, ProviderStatus.ready)
    provider.status = ProviderStatus.ready
    provider.updated_by = updated_by
    session.add(provider)
    session.commit()


def is_provider_ready(provider: Provider) -> bool:
    """Check if a given provider is ready.

    Verify that the root project and its SLA are set, and that the provider has at least
    one region and one identity provider (IdP).

    Args:
        provider (Provider): The provider instance to check.

    Returns:
        bool: True if the provider is ready, False otherwise.

    """
    return (
        provider.root_project is not None
        and provider.root_project.sla is not None
        and len(provider.regions) > 0
        and len(provider.idps) > 0
    )


def provider_can_be_evaluated(provider: Provider) -> bool:
    """Check if a given provider is ready.

    Verify that the root project and its SLA are set, and that the provider has at least
    one region and one identity provider (IdP).

    Args:
        provider (Provider): The provider instance to check.

    Returns:
        bool: True if the provider is ready, False otherwise.

    """
    return len(provider.site_testers) > 0


async def update_provider_status(provider: Provider) -> Provider:
    """Update the status of a Provider instance based on its attributes.

    Transitions the provider's status according to the following rules:
    - If the status is 'draft' and the provider has a root project with an SLA, at least
        one region, and at least one IDP, the status is set to 'ready'.
    - If the status is 'ready' and the provider is missing a root project, an SLA, any
        regions, or any IDPs, the status is set back to 'draft'.

    Args:
        provider (Provider): The provider instance whose status will be updated.

    Returns:
        None

    """
    settings = get_settings()
    logger = get_logger(settings)
    match provider.status:
        case ProviderStatus.draft:
            if is_provider_ready(provider):
                provider.status = ProviderStatus.ready
        case ProviderStatus.ready:
            if not is_provider_ready(provider):
                provider.status = ProviderStatus.draft
        case ProviderStatus.submitted:
            if provider_can_be_evaluated(provider):
                provider.status = ProviderStatus.evaluation
                await send_provider_to_be_evaluated(provider, settings, logger)
    return provider


@event.listens_for(Provider, "before_update")
async def before_update_provider(mapper, connection, provider: Provider):
    """Listen for the 'before_update' event.

    Apply automatic state changes when all conditions are met:
    - advance from draft to ready
    - revert from ready to draft
    - advance from submit to evaluation and send message to kafka
    """
    await update_provider_status(provider)
