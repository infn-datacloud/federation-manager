"""Endpoints to manage identity provider details."""

import urllib.parse
import uuid

from fastapi import APIRouter, HTTPException, Request, Response, Security, status

from fed_mgr.auth import check_authorization
from fed_mgr.db import SessionDep
from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    NoItemToUpdateError,
    NotNullError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import IDPS_PREFIX, USER_GROUPS_PREFIX
from fed_mgr.v1.identity_providers.crud import add_idp, delete_idp, get_idps, update_idp
from fed_mgr.v1.identity_providers.dependencies import IdentityProviderDep
from fed_mgr.v1.identity_providers.schemas import (
    IdentityProviderCreate,
    IdentityProviderList,
    IdentityProviderQueryDep,
    IdentityProviderRead,
)
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.dependencies import CurrenUserDep

idp_router = APIRouter(
    prefix=IDPS_PREFIX,
    tags=["identity providers"],
    dependencies=[Security(check_authorization)],
)


@idp_router.options(
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

    """
    add_allow_header_to_resp(idp_router, response)


@idp_router.post(
    "/",
    summary="Create a new identity provider",
    description="Add a new identity provider to the DB. Check if a identity provider's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
    },
)
def create_idp(
    request: Request,
    session: SessionDep,
    idp: IdentityProviderCreate,
    current_user: CurrenUserDep,
) -> ItemID:
    """Create a new identity provider in the system.

    Logs the creation attempt and result. If the identity provider already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the identity provider data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        idp (IdentityProviderCreate | None): The identity provider data to create.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        session (SessionDep): The database session dependency.

    Returns:
        ItemID: A dictionary containing the ID of the created identity provider on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Creating identity provider with params: {idp.model_dump_json()}"
    request.state.logger.info(msg)
    try:
        db_idp = add_idp(session=session, idp=idp, created_by=current_user)
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
    msg = f"Identity Provider created: {db_idp.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_idp.id}


@idp_router.get(
    "/",
    summary="Retrieve identity providers",
    description="Retrieve a paginated list of identity providers.",
)
def retrieve_idps(
    request: Request, params: IdentityProviderQueryDep, session: SessionDep
) -> IdentityProviderList:
    """Retrieve a paginated list of identity providers based on query parameters.

    Logs the query parameters and the number of identity providers retrieved. Fetches
    identity providers from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the identity providers in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (IdentityProviderQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.

    Returns:
        IdentityProviderList: A paginated list of identity providers matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retrieve identity providers. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    idps, tot_items = get_idps(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved identity providers: "
    msg += f"{[idp.model_dmp_json() for idp in idps]}"
    request.state.logger.info(msg)
    new_idps = []
    for idp in idps:
        new_idp = IdentityProviderRead(
            **idp.model_dump(),  # Does not return created_by and updated_by
            created_by=idp.created_by_id,
            updated_by=idp.created_by_id,
            links={
                "user_groups": urllib.parse.urljoin(
                    str(request.url), f"{idp.id}{USER_GROUPS_PREFIX}"
                )
            },
        )
        new_idps.append(new_idp)
    return IdentityProviderList(
        data=new_idps,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@idp_router.get(
    "/{idp_id}",
    summary="Retrieve identity provider with given ID",
    description="Check if the given identity provider's ID already exists in the DB "
    "and return it. If the identity provider does not exist in the DB, the endpoint "
    "raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_idp(
    request: Request, idp_id: uuid.UUID, idp: IdentityProviderDep
) -> IdentityProviderRead:
    """Retrieve a identity provider by their unique identifier.

    Logs the retrieval attempt, checks if the identity provider exists, and returns the
    identity provider object if found. If the identity provider does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        idp_id (uuid.UUID): The unique identifier of the identity provider to retrieve.
        idp (IdentityProvider | None): The identity provider object, if found.

    Returns:
        IdentityProvider: The identity provider object if found.
        JSONResponse: A 404 response if the identity provider does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = f"Retrieve identity provider with ID '{idp_id!s}'"
    request.state.logger.info(msg)
    if idp is None:
        msg = f"Identity Provider with ID '{idp_id!s}' does not exist"
        request.state.logger.error(msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    msg = f"Identity Provider with ID '{idp_id!s}' found: {idp.model_dump_json()}"
    request.state.logger.info(msg)
    idp = IdentityProviderRead(
        **idp.model_dump(),  # Does not return created_by and updated_by
        created_by=idp.created_by_id,
        updated_by=idp.created_by_id,
        links={
            "user_groups": urllib.parse.urljoin(
                str(request.url), f"{idp_id}{USER_GROUPS_PREFIX}"
            )
        },
    )
    return idp


@idp_router.put(
    "/{idp_id}",
    summary="Update identity provider with the given id",
    description="Update a identity provider with the given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_idp(
    request: Request,
    idp_id: uuid.UUID,
    new_idp: IdentityProviderCreate,
    session: SessionDep,
    current_user: CurrenUserDep,
) -> None:
    """Update an existing identity provider in the database with the given idp ID.

    Args:
        request (Request): The current request object.
        idp_id (uuid.UUID): The unique identifier of the identity provider to update.
        new_idp (UserCreate): The new identity provider data to update.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.

    Raises:
        HTTPException: If the identity provider is not found or another update error
        occurs.

    """
    msg = f"Update identity provider with ID '{idp_id!s}'"
    request.state.logger.info(msg)
    try:
        update_idp(
            session=session, idp_id=idp_id, new_idp=new_idp, updated_by=current_user
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
    msg = f"Identity Provider with ID '{idp_id!s}' updated"
    request.state.logger.info(msg)


@idp_router.delete(
    "/{idp_id}",
    summary="Delete identity provider with given sub",
    description="Delete a identity provider with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_idp(request: Request, idp_id: uuid.UUID, session: SessionDep) -> None:
    """Remove a identity provider from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_idp`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        idp_id (uuid.UUID): The unique identifier of the identity provider to be removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Delete identity provider with ID '{idp_id!s}'"
    request.state.logger.info(msg)
    try:
        delete_idp(session=session, idp_id=idp_id)
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Identity Provider with ID '{idp_id!s}' deleted"
    request.state.logger.info(msg)
