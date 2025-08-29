"""Project CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete provider' projects in
the database. It wraps generic CRUD operations with projects-specific logic
and exception handling.
"""

import uuid

from sqlmodel import Session

from fed_mgr.db import SessionDep
from fed_mgr.v1.crud import add_item, delete_item, get_item, get_items, update_item
from fed_mgr.v1.models import Project, Provider, User
from fed_mgr.v1.providers.projects.schemas import ProjectCreate


def get_project(*, session: SessionDep, project_id: uuid.UUID) -> Project | None:
    """Retrieve an project by their unique project_id from the database.

    Args:
        project_id: The UUID of the project to retrieve.
        session: The database session dependency.

    Returns:
        Project instance if found, otherwise None.

    """
    return get_item(session=session, entity=Project, id=project_id)


def get_projects(
    *, session: Session, skip: int, limit: int, sort: str, **kwargs
) -> tuple[list[Project], int]:
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
        Tuple of (list of Project instances, total count of matching projects).

    """
    return get_items(
        session=session,
        entity=Project,
        skip=skip,
        limit=limit,
        sort=sort,
        **kwargs,
    )


def add_project(
    *, session: Session, project: ProjectCreate, created_by: User, provider: Provider
) -> Project:
    """Add a new project to the database.

    Args:
        session: The database session.
        project: The ProjectCreate model instance to add.
        created_by: The User instance representing the creator of the project.
        provider: The project's parent provider.

    Returns:
        Project: The identifier of the newly created project.

    """
    return add_item(
        session=session,
        entity=Project,
        created_by=created_by,
        updated_by=created_by,
        provider=provider,
        **project.model_dump(),
    )


def update_project(
    *,
    session: Session,
    project_id: uuid.UUID,
    new_project: ProjectCreate,
    updated_by: User,
) -> None:
    """Update an project by their unique project_id from the database.

    Override only a subset of the project entity attributes.

    Args:
        session: The database session.
        project_id: The UUID of the project to update.
        new_project: The new data to update the project with.
        updated_by: The User instance representing the updater of the project.

    Returns:
        None

    """
    return update_item(
        session=session,
        entity=Project,
        id=project_id,
        updated_by=updated_by,
        **new_project.model_dump(),
    )


def delete_project(*, session: Session, project_id: uuid.UUID) -> None:
    """Delete a project by their unique project_id from the database.

    Args:
        session: The database session.
        project_id: The UUID of the project to delete.

    Returns:
        None

    """
    delete_item(session=session, entity=Project, id=project_id)
