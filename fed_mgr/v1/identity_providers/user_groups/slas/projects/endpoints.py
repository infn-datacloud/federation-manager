"""Endpoints to manage sla details."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from fed_mgr.db import SessionDep
from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    ItemNotFoundError,
    NotNullError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import IDPS_PREFIX, PROJECTS_PREFIX, SLAS_PREFIX, USER_GROUPS_PREFIX
from fed_mgr.v1.identity_providers.dependencies import idp_required
from fed_mgr.v1.identity_providers.user_groups.dependencies import user_group_required
from fed_mgr.v1.identity_providers.user_groups.slas.dependencies import (
    SLARequiredDep,
    sla_required,
)
from fed_mgr.v1.identity_providers.user_groups.slas.projects.crud import (
    connect_proj_to_sla,
    disconnect_proj_from_sla,
)
from fed_mgr.v1.identity_providers.user_groups.slas.projects.schemas import (
    ProjSLAConnectionCreate,
)
from fed_mgr.v1.providers.endpoints import update_provider_state
from fed_mgr.v1.providers.projects.crud import get_project
from fed_mgr.v1.providers.projects.dependencies import ProjectRequiredDep
from fed_mgr.v1.providers.schemas import ProviderStatus
from fed_mgr.v1.schemas import ErrorMessage
from fed_mgr.v1.users.dependencies import CurrenUserDep

sla_proj_conn_router = APIRouter(
    prefix=IDPS_PREFIX
    + "/{idp_id}"
    + USER_GROUPS_PREFIX
    + "/{user_group_id}"
    + SLAS_PREFIX
    + "/{sla_id}"
    + PROJECTS_PREFIX,
    tags=["sla's projects"],
    dependencies=[
        Depends(idp_required),
        Depends(user_group_required),
        Depends(sla_required),
    ],
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)


@sla_proj_conn_router.options(
    "/",
    summary="List available endpoints for this resource",
    description="List available endpoints for this resource in the 'Allow' header.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def available_methods(response: Response) -> None:
    """Add the HTTP 'Allow' header to the response.

    Args:
        response (Response): The HTTP response object to which the 'Allow' header will
            be added.

    Returns:
        None

    Raises:
        404 Not Found: If the parent user group does not exists.

    """
    add_allow_header_to_resp(sla_proj_conn_router, response)


@sla_proj_conn_router.post(
    "/",
    summary="Create a new sla",
    description="Add a new sla to the DB. Check if a sla's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorMessage},
    },
)
def connect_sla_to_proj(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    sla: SLARequiredDep,
    config: ProjSLAConnectionCreate,
) -> None:
    """Create a new sla in the system.

    Logs the creation attempt and result. If the sla already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the sla data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (SessionDep): The database session dependency.
        sla (SLA): The sla data to create.
        current_user (CurrenUser): The DB user matching the current user retrieved
            from the access token.
        config (UserGroup): The parent user group associated with the sla.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the parent identity provider does not exists.
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Connecting SLA with ID '{sla.id!s}' to Project with ID "
    msg += f"'{config.project_id!s}'"
    request.state.logger.info(msg)
    try:
        project = get_project(session=session, project_id=config.project_id)
        if project is None:
            raise ItemNotFoundError("Project", id=config.project_id)
        connect_proj_to_sla(
            session=session, updated_by=current_user, sla=sla, project=project
        )
    except ItemNotFoundError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        ) from e
    except ConflictError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        ) from e
    except NotNullError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=e.message
        ) from e
    msg = f"SLA with ID '{sla.id!s}' connected to Project with ID "
    msg += f"'{config.project_id!s}'"
    request.state.logger.info(msg)

    update_provider_state(
        request=request,
        session=session,
        provider=project.provider,
        current_user=current_user,
        next_state=ProviderStatus.ready,
    )


@sla_proj_conn_router.delete(
    "/{project_id}",
    summary="Delete sla with given sub",
    description="Delete a sla with the given subject, for this issuer, from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage}},
)
def disconnect_sla_from_project(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    sla: SLARequiredDep,
    project: ProjectRequiredDep,
) -> None:
    """Remove a sla from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the
    `delete_sla` function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        sla (uuid.UUID): The unique identifier of the sla to be removed
        project (uuid.UUID): The unique identifier of the sla to be removed
        current_user (uuid.UUID): The unique identifier of the sla to be removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the parent identity provider does not exists.

    """
    msg = f"Disconnect project with ID '{project.id!s}' from SLA with ID '{sla.id!s}"
    request.state.logger.info(msg)
    try:
        disconnect_proj_from_sla(
            session=session, updated_by=current_user, project=project
        )
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Project with ID '{project.id!s}' disconnected from SLA with ID '{sla.id!s}"
    request.state.logger.info(msg)
