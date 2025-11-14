"""SLA CRUD utility functions for fed-mgr service.

This module provides functions to retrieve, list, add, and delete slas in
the database. It wraps generic CRUD operations with slas-specific logic
and exception handling.
"""

from sqlmodel import Session

from fed_mgr.exceptions import DeleteFailedError
from fed_mgr.v1.models import SLA, Project, User
from fed_mgr.v1.providers.schemas import ProviderStatus


def connect_proj_to_sla(
    *, session: Session, updated_by: User, project: Project, sla: SLA
) -> None:
    """Associates a given SLA (Service Level Agreement) with a project.

    If the project already has an SLA associated, overwrite the existing one.

    If the project is the root one and the provider is in the `draft` state, update the
    provider state to `ready`.

    Args:
        session (SessionDep): The database session used for committing changes.
        updated_by (User): The user performing the update.
        project (Project): The project instance to be updated.
        sla (SLA): The SLA instance to associate with the project.

    Returns:
        None

    """
    if project.is_root and project.provider.status == ProviderStatus.draft:
        project.provider.status = ProviderStatus.ready
    project.sla = sla
    project.updated_by = updated_by
    session.add(project)
    session.commit()


def disconnect_proj_from_sla(
    *, session: Session, updated_by: User, project: Project
) -> None:
    """Disconnect a project from its associated SLA.

    If the project is the root one and the hosting provider is not in the `ready` state,
    raise a ConflictError.

    If the project it the root one and the hosting provider is in the `ready` state,
    update the provider state to `draft`.

    If the project it the root one and the hosting provider is in the `ready` state, or
    the project is not the root one (independently of the provider's state) sets the
    `sla` attribute of the given `project` to `None`, updates the `updated_by` field,
    and commits the changes to the database session.

    Args:
        session (Session): The SQLAlchemy session used to commit the changes.
        updated_by (User): The user performing the update.
        project (Project): The project to disconnect from its SLA.

    Returns:
        None

    """
    if project.is_root and project.provider.status != ProviderStatus.ready:
        raise DeleteFailedError(
            "The SLA of the root project can't be removed if the hosting provider is "
            f"not in the {ProviderStatus.ready.name} state"
        )
    if project.is_root:
        project.provider.status = ProviderStatus.draft
    project.sla = None
    project.updated_by = updated_by
    session.add(project)
    session.commit()
