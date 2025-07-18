"""Region CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete regions in the
database. It wraps generic CRUD operations with resource regions-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.exceptions import LocationNotFoundError
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.locations.crud import get_location
from fed_mgr.v1.models import Location, Provider, Region, User
from fed_mgr.v1.providers.regions.schemas import RegionCreate


def get_region(*, session: SessionDep, region_id: uuid.UUID) -> Region | None:
    """Retrieve an region by their unique region_id from the database.

    Args:
        region_id: The UUID of the region to retrieve.
        session: The database session dependency.

    Returns:
        Region instance if found, otherwise None.

    """
    return get_item(session=session, entity=Region, id=region_id)


def get_regions(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[Region], int]:
    """Retrieve a paginated and sorted list of regions from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed regions since they are paginated.

    Args:
        session: The database session.
        skip: Number of regions to skip (for pagination).
        limit: Maximum number of regions to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of Region instances, total count of matching regions).

    """
    return get_items(
        session=session,
        entity=Region,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_region(
    *, session: Session, region: RegionCreate, created_by: User, provider: Provider
) -> Region:
    """Add a new region to the database.

    Args:
        session: The database session.
        region: The RegionCreate model instance to add.
        created_by: The User instance representing the creator of the region.
        provider: The region's parent provider.

    Returns:
        Region: The identifier of the newly created region.

    """
    location = check_location_exist(session=session, region=region)
    return add_item(
        session=session,
        entity=Region,
        created_by=created_by,
        updated_by=created_by,
        provider=provider,
        location=location,
        **region.model_dump(),
    )


def update_region(
    *,
    session: Session,
    region_id: uuid.UUID,
    new_region: RegionCreate,
    updated_by: User,
) -> None:
    """Update an region by their unique region_id from the database.

    Override only a subset of the region entity attributes.

    Args:
        session: The database session.
        region_id: The UUID of the region to update.
        new_region: The new data to update the region with.
        updated_by: The User instance representing the updater of the region.

    Returns:
        None

    """
    check_location_exist(session=session, region=new_region)
    return update_item(
        session=session,
        entity=Region,
        id=region_id,
        updated_by=updated_by,
        **new_region.model_dump(),
    )


def delete_region(*, session: Session, region_id: uuid.UUID) -> None:
    """Delete a region by their unique region_id from the database.

    Args:
        session: The database session.
        region_id: The UUID of the region to delete.

    Returns:
        None

    """
    delete_item(session=session, entity=Region, id=region_id)


def check_location_exist(session: Session, region: RegionCreate) -> Location:
    """Check if location ID exists in the database.

    Args:
        session (Session): The database session used to query users.
        region (RegionCreate): The region object containing the location ID.

    Returns:
        Location: the location DB object.

    Raises:
        LocationNotFoundError: If the location ID does not exist in the database.

    """
    location = get_location(session=session, location_id=region.location_id)
    if location is None:
        raise LocationNotFoundError(
            f"Location with ID '{region.location_id!s}' does not exist"
        )
    return location
