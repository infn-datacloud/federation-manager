"""SLA CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete slas in
the database. It wraps generic CRUD operations with slas-specific logic
and exception handling.
"""

from sqlmodel import Session

from fed_mgr.v1.models import SLA, Project, User


def connect_proj_to_sla(
    *, session: Session, updated_by: User, project: Project, sla: SLA
) -> None:
    """Associates a given SLA (Service Level Agreement) with a project.

    Args:
        session (SessionDep): The database session used for committing changes.
        updated_by (User): The user performing the update.
        project (Project): The project instance to be updated.
        sla (SLA): The SLA instance to associate with the project.

    Returns:
        None

    """
    project.sla = sla
    project.updated_by = updated_by
    session.add(project)
    session.commit()


def disconnect_proj_from_sla(
    *, session: Session, updated_by: User, project: Project
) -> None:
    """Disconnect a project from its associated SLA.

    This function sets the `sla` attribute of the given `project` to `None`, updates the
    `updated_by` field, and commits the changes to the database session.

    Args:
        session (Session): The SQLAlchemy session used to commit the changes.
        updated_by (User): The user performing the update.
        project (Project): The project to disconnect from its SLA.

    Returns:
        None

    """
    project.sla = None
    project.updated_by = updated_by
    session.add(project)
    session.commit()
