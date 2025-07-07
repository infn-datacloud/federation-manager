"""Location CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete locations in
the database. It wraps generic CRUD operations with locations-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.locations.schemas import LocationCreate
from fed_mgr.v1.models import Location, User


def get_location(*, session: SessionDep, location_id: uuid.UUID) -> Location | None:
    """Retrieve a location by their unique location_id from the database.

    Args:
        location_id: The UUID of the location to retrieve.
        session: The database session dependency.

    Returns:
        Location instance if found, otherwise None.

    """
    return get_item(session=session, entity=Location, id=location_id)


def get_locations(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[Location], int]:
    """Retrieve a paginated and sorted list of locations from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed locations since they are paginated.

    Args:
        session: The database session.
        skip: Number of locations to skip (for pagination).
        limit: Maximum number of locations to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of Location instances, total count of matching locations).

    """
    return get_items(
        session=session,
        entity=Location,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_location(
    *, session: Session, location: LocationCreate, created_by: User
) -> Location:
    """Add a new location to the database.

    Args:
        session: The database session.
        location: The LocationCreate model instance to add.
        created_by: The User instance representing the creator of the location.

    Returns:
        Location: The identifier of the newly created location.

    """
    return add_item(
        session=session,
        entity=Location,
        created_by=created_by,
        updated_by=created_by,
        **location.model_dump(),
    )


def update_location(
    *,
    session: Session,
    location_id: uuid.UUID,
    new_location: LocationCreate,
    updated_by: User,
) -> None:
    """Update an location by their unique location_id from the database.

    Completely override an location entity.

    Args:
        session: The database session.
        location_id: The UUID of the location to update.
        new_location: The new data to update the location with.
        updated_by: The User instance representing the updater of the location.

    """
    return update_item(
        session=session,
        entity=Location,
        id=location_id,
        updated_by=updated_by,
        **new_location.model_dump(),
    )


def delete_location(*, session: Session, location_id: uuid.UUID) -> None:
    """Delete a location by their unique location_id from the database.

    Args:
        session: The database session.
        location_id: The UUID of the location to delete.

    """
    delete_item(session=session, entity=Location, id=location_id)
