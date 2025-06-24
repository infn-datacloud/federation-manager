"""SLA CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete slas in
the database. It wraps generic CRUD operations with slas-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.identity_providers.user_groups.schemas import UserGroup
from fed_mgr.v1.identity_providers.user_groups.slas.schemas import SLA, SLACreate
from fed_mgr.v1.schemas import ItemID
from fed_mgr.v1.users.schemas import User


def get_sla(
    *, session: SessionDep, sla_id: uuid.UUID
) -> SLA | None:
    """Retrieve an sla by their unique sla_id from the database.

    Args:
        sla_id: The UUID of the sla to retrieve.
        session: The database session dependency.

    Returns:
        SLA instance if found, otherwise None.

    """
    return get_item(session=session, entity=SLA, item_id=sla_id)


def get_slas(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[SLA], int]:
    """Retrieve a paginated and sorted list of slas from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed slas since they are paginated.

    Args:
        session: The database session.
        skip: Number of slas to skip (for pagination).
        limit: Maximum number of slas to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of SLA instances, total count of matching identity
        providers).

    """
    return get_items(
        session=session,
        entity=SLA,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_sla(
    *,
    session: Session,
    sla: SLACreate,
    created_by: User,
    parent_user_group: UserGroup,
) -> ItemID:
    """Add a new sla to the database.

    Args:
        session: The database session.
        sla: The SLACreate model instance to add.
        created_by: The User istance representing the creator of the SLA.
        parent_user_group: The sla's parent user group.

    Returns:
        ItemID: The identifier of the newly created sla.

    """
    return add_item(
        session=session,
        entity=SLA,
        item=sla,
        created_by=created_by.id,
        updated_by=created_by.id,
        user_group=parent_user_group.id,
    )


def update_sla(
    *,
    session: Session,
    sla_id: uuid.UUID,
    new_sla: SLACreate,
    updated_by: User,
) -> None:
    """Update an sla by their unique sla_id from the database.

    Completely override an sla entity.

    Args:
        session: The database session.
        sla_id: The UUID of the sla to update.
        new_sla: The new data to update the sla with.
        updated_by: The User instance representing the updater of the sla.

    """
    return update_item(
        session=session,
        entity=SLA,
        item_id=sla_id,
        new_data=new_sla,
        updated_by=updated_by.id,
    )


def delete_sla(*, session: Session, sla_id: uuid.UUID) -> None:
    """Delete a sla by their unique sla_id from the database.

    Args:
        session: The database session.
        sla_id: The UUID of the sla to delete.

    """
    delete_item(session=session, entity=SLA, item_id=sla_id)
