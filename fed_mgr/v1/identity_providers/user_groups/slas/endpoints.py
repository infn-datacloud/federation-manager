"""Endpoints to manage sla details."""

import urllib.parse
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    Security,
    status,
)

from fed_mgr.auth import check_authorization
from fed_mgr.db import SessionDep
from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    NoItemToUpdateError,
    NotNullError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import IDPS_PREFIX, PROJECTS_PREFIX, SLAS_PREFIX, USER_GROUPS_PREFIX
from fed_mgr.v1.identity_providers.dependencies import idp_required
from fed_mgr.v1.identity_providers.user_groups.dependencies import (
    UserGroupDep,
    user_group_required,
)
from fed_mgr.v1.identity_providers.user_groups.slas.crud import (
    add_sla,
    delete_sla,
    get_slas,
    update_sla,
)
from fed_mgr.v1.identity_providers.user_groups.slas.dependencies import SLADep
from fed_mgr.v1.identity_providers.user_groups.slas.schemas import (
    SLACreate,
    SLAList,
    SLAQueryDep,
    SLARead,
)
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.dependencies import CurrenUserDep

sla_router = APIRouter(
    prefix=IDPS_PREFIX
    + "/{idp_id}"
    + USER_GROUPS_PREFIX
    + "/{user_group_id}"
    + SLAS_PREFIX,
    tags=["slas"],
    dependencies=[
        Security(check_authorization),
        Depends(idp_required),
        Depends(user_group_required),
    ],
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)


@sla_router.options(
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
    add_allow_header_to_resp(sla_router, response)


@sla_router.post(
    "/",
    summary="Create a new sla",
    description="Add a new sla to the DB. Check if a sla's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
    },
)
def create_sla(
    request: Request,
    session: SessionDep,
    sla: SLACreate,
    current_user: CurrenUserDep,
    user_group: UserGroupDep,
) -> ItemID:
    """Create a new sla in the system.

    Logs the creation attempt and result. If the sla already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the sla data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (SessionDep): The database session dependency.
        sla (SLACreate | None): The sla data to create.
        current_user (CurrenUser): The DB user matching the current user retrieved
            from the access token.
        user_group (UserGroup): The parent user group associated with the sla.

    Returns:
        ItemID: A dictionary containing the ID of the created sla on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the parent identity provider does not exists.
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Creating SLA with params: {sla.model_dump_json()}"
    request.state.logger.info(msg)
    try:
        db_sla = add_sla(
            session=session, sla=sla, created_by=current_user, user_group=user_group
        )
    except ConflictError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        ) from e
    except NotNullError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    msg = f"User created: {db_sla.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_sla.id}


@sla_router.get(
    "/",
    summary="Retrieve slas",
    description="Retrieve a paginated list of slas.",
)
def retrieve_slas(
    request: Request, params: SLAQueryDep, session: SessionDep, user_group_id: uuid.UUID
) -> SLAList:
    """Retrieve a paginated list of slas based on query parameters.

    Logs the query parameters and the number of slas retrieved. Fetches
    slas from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the slas in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (SLAQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.
        user_group_id: Parent user group ID

    Returns:
        SLAList: A paginated list of slas matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the parent identity provider does not exists.

    """
    msg = f"Retrieve SLAs. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    slas, tot_items = get_slas(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        user_group_id=user_group_id,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved SLAs: {[sla.model_dump_json() for sla in slas]}"
    request.state.logger.info(msg)
    new_slas = []
    for sla in slas:
        new_sla = SLARead(
            **sla.model_dump(),  # Does not return created_by and updated_by
            created_by=sla.created_by_id,
            updated_by=sla.created_by_id,
            links={
                "projects": urllib.parse.urljoin(
                    str(request.url), f"{sla.id}{PROJECTS_PREFIX}"
                )
            },
        )
        new_slas.append(new_sla)
    return SLAList(
        data=new_slas,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@sla_router.get(
    "/{sla_id}",
    summary="Retrieve sla with given ID",
    description="Check if the given sla's ID already exists in the DB "
    "and return it. If the sla does not exist in the DB, the endpoint "
    "raises a 404 error.",
)
def retrieve_sla(request: Request, sla_id: uuid.UUID, sla: SLADep) -> SLARead:
    """Retrieve a sla by their unique identifier.

    Logs the retrieval attempt, checks if the sla exists, and returns the
    sla object if found. If the sla does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        sla_id (uuid.UUID): The unique identifier of the sla to retrieve.
        sla (SLA | None): The sla object, if found.

    Returns:
        SLA: The sla object if found.
        JSONResponse: A 404 response if the sla does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = f"Retrieve SLA with ID '{sla_id!s}'"
    request.state.logger.info(msg)
    if sla is None:
        msg = f"SLA with ID '{sla_id!s}' does not exist"
        request.state.logger.error(msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    msg = f"SLA with ID '{sla_id!s}' found: {sla.model_dump_json()}"
    request.state.logger.info(msg)
    sla = SLARead(
        **sla.model_dump(),  # Does not return created_by and updated_by
        created_by=sla.created_by_id,
        updated_by=sla.created_by_id,
        links={
            "projects": urllib.parse.urljoin(
                str(request.url), f"{sla_id}{PROJECTS_PREFIX}"
            )
        },
    )
    return sla


@sla_router.put(
    "/{sla_id}",
    summary="Update sla with the given id",
    description="Update a sla with the given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_sla(
    request: Request,
    sla_id: uuid.UUID,
    new_sla: SLACreate,
    session: SessionDep,
    current_user: CurrenUserDep,
) -> None:
    """Update an existing sla in the database with the given sla ID.

    Args:
        request (Request): The current request object.
        sla_id (uuid.UUID): The unique identifier of the sla to update.
        new_sla (UserCreate): The new sla data to update.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.

    Raises:
        404 Not Found: If the parent identity provider does not exists, if the user
            group is not found

    """
    msg = f"Update SLA with ID '{sla_id!s}'"
    request.state.logger.info(msg)
    try:
        update_sla(
            session=session,
            sla_id=sla_id,
            new_sla=new_sla,
            updated_by=current_user,
        )
    except NoItemToUpdateError as e:
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    msg = f"SLA with ID '{sla_id!s}' updated"
    request.state.logger.info(msg)


@sla_router.delete(
    "/{sla_id}",
    summary="Delete sla with given sub",
    description="Delete a sla with the given subject, for this issuer, from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_sla(request: Request, sla_id: uuid.UUID, session: SessionDep) -> None:
    """Remove a sla from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the
    `delete_sla` function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        sla_id (uuid.UUID): The unique identifier of the sla to be removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the parent identity provider does not exists.

    """
    msg = f"Delete SLA with ID '{sla_id!s}'"
    request.state.logger.info(msg)
    try:
        delete_sla(session=session, sla_id=sla_id)
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"SLA with ID '{sla_id!s}' deleted"
    request.state.logger.info(msg)
