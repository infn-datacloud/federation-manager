"""ProjRegConfig CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete provider' projects in
the database. It wraps generic CRUD operations with projects-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.models import Project, ProjRegConfig, Region, User
from fed_mgr.v1.providers.projects.regions.schemas import ProjRegConfigCreate


def get_project_config(
    *, session: SessionDep, project_id: uuid.UUID, region_id: uuid.UUID
) -> ProjRegConfig | None:
    """Retrieve an project config for a specific region.

    Use the unique project_id and region id to retrieve the config from the database.

    Args:
        session: The database session dependency.
        project_id: The UUID of the project to retrieve.
        region_id: The UUID of the region to retrieve.

    Returns:
        ProjRegConfig instance if found, otherwise None.

    """
    return get_item(
        session=session,
        entity=ProjRegConfig,
        project_id=project_id,
        region_id=region_id,
    )


def get_project_configs(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[ProjRegConfig], int]:
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
        Tuple of (list of ProjRegConfig instances, total count of matching projects).

    """
    return get_items(
        session=session,
        entity=ProjRegConfig,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_project_config(
    *,
    session: Session,
    overrides: ProjRegConfigCreate,
    created_by: User,
    project: Project,
    region: Region,
) -> ProjRegConfig:
    """Add a new project to the database.

    Args:
        session: The database session.
        project: The project's parent provider.
        region: The target region to link.
        overrides: The ProjRegConfigCreate model instance to add.
        created_by: The User instance representing the creator of the project.

    Returns:
        ProjRegConfig: The identifier of the newly created project.

    """
    return add_item(
        session=session,
        entity=ProjRegConfig,
        project=project,
        region=region,
        created_by=created_by,
        updated_by=created_by,
        **overrides.model_dump(),
    )


def update_project_config(
    *,
    session: Session,
    project_id: uuid.UUID,
    region_id: uuid.UUID,
    new_overrides: ProjRegConfigCreate,
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
        entity=ProjRegConfig,
        project_id=project_id,
        region_id=region_id,
        updated_by=updated_by,
        **new_overrides.model_dump(exclude_none=True),
    )


def delete_project_config(
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
    delete_item(
        session=session,
        entity=ProjRegConfig,
        project_id=project_id,
        region_id=region_id,
    )
