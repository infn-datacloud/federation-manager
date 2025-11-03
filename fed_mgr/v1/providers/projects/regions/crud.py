"""RegionOverrides CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete provider' projects in
the database. It wraps generic CRUD operations with projects-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.models import Project, RegionOverrides, User
from fed_mgr.v1.providers.projects.regions.schemas import (
    ProjRegConnectionCreate,
    RegionOverridesBase,
)
from fed_mgr.v1.providers.regions.crud import get_region


def get_region_overrides(
    *, session: SessionDep, project_id: uuid.UUID, region_id: uuid.UUID
) -> RegionOverrides | None:
    """Retrieve an project config for a specific region.

    Use the unique project_id and region id to retrieve the config from the database.

    Args:
        session: The database session dependency.
        project_id: The UUID of the project to retrieve.
        region_id: The UUID of the region to retrieve.

    Returns:
        RegionOverrides instance if found, otherwise None.

    """
    return get_item(
        session=session,
        entity=RegionOverrides,
        project_id=project_id,
        region_id=region_id,
    )


def get_region_overrides_list(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[RegionOverrides], int]:
    """Retrieve a paginated and sorted list of projects from the database.

    The total count corresponds to the total count of returned values which may differs
    from the showed projects since they are paginated.

    Args:
        session: The database session.
        skip: Number of projects to skip (for pagination).
        limit: Maximum number of projects to return.
        sort: Field name to sort by (prefix with '-' for descending).
        **kwargs: Additional filter parameters for narrowing the search.

    Returns:
        Tuple of (list of RegionOverrides instances, total count of matching projects).

    """
    return get_items(
        session=session,
        entity=RegionOverrides,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def connect_project_region(
    *,
    session: Session,
    config: ProjRegConnectionCreate,
    created_by: User,
    project: Project,
) -> RegionOverrides:
    """Add a new project to the database.

    Args:
        session: The database session.
        project: The project's parent provider.
        config: The RegionOverridesCreate model instance to add.
        created_by: The User instance representing the creator of the project.

    Returns:
        RegionOverrides: The identifier of the newly created project.

    """
    region = get_region(session=session, region_id=config.region_id)
    if region is None:
        raise ItemNotFoundError(f"Region with ID '{config.region_id}' does not exist")
    return add_item(
        session=session,
        entity=RegionOverrides,
        project=project,
        region=region,
        created_by=created_by,
        updated_by=created_by,
        **config.overrides.model_dump(),
    )


def update_region_overrides(
    *,
    session: Session,
    project_id: uuid.UUID,
    region_id: uuid.UUID,
    new_overrides: RegionOverridesBase,
    updated_by: User,
) -> None:
    """Update an project by their unique project_id from the database.

    Override only a subset of the project entity attributes.

    Args:
        session: The database session.
        project_id: The UUID of the target project.
        region_id: The UUID of the involved region.
        new_overrides: The new data to update the project with.
        updated_by: The User instance representing the updater of the project.

    Returns:
        None

    """
    return update_item(
        session=session,
        entity=RegionOverrides,
        project_id=project_id,
        region_id=region_id,
        updated_by=updated_by,
        **new_overrides.model_dump(),
    )


def disconnect_project_region(
    *, session: Session, project_id: uuid.UUID, region_id: uuid.UUID
) -> None:
    """Delete a project by their unique project_id from the database.

    Args:
        session: The database session.
        project_id: The UUID of the project to delete.
        region_id: The UUID of the region to delete.

    Returns:
        None

    """
    return delete_item(
        session=session,
        entity=RegionOverrides,
        project_id=project_id,
        region_id=region_id,
    )
