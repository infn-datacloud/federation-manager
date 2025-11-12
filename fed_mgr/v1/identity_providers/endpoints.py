"""Endpoints to manage identity provider details.

This module defines the API endpoints for managing identity providers. It includes
operations for creating, retrieving, updating, and deleting identity providers, as well
as listing available endpoints and retrieving paginated lists of identity providers.

Routes:
    - OPTIONS /identity-providers: List available endpoints for this resource.
    - POST /identity-providers: Create a new identity provider.
    - GET /identity-providers: Retrieve a paginated list of identity providers.
    - GET /identity-providers/{idp_id}: Retrieve a specific identity provider by ID.
    - PUT /identity-providers/{idp_id}: Update an existing identity provider by ID.
    - DELETE /identity-providers/{idp_id}: Delete an identity provider by ID.

Dependencies:
    - SessionDep: Provides a database session.
    - CurrentUserDep: Provides the current authenticated user.
    - IdentityProviderRequiredDep: Ensures the identity provider exists.

Exceptions:
    - ConflictError: Raised when a conflict occurs (e.g., duplicate identity provider).
    - NotNullError: Raised when a required field is null.
    - ItemNotFoundError: Raised when an item is not found.
    - DeleteFailedError: Raised when deletion fails.

"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, status

from fed_mgr.db import SessionDep
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import IDPS_PREFIX
from fed_mgr.v1.identity_providers.crud import add_idp, delete_idp, get_idps, update_idp
from fed_mgr.v1.identity_providers.dependencies import IdentityProviderRequiredDep
from fed_mgr.v1.identity_providers.schemas import (
    IdentityProviderCreate,
    IdentityProviderList,
    IdentityProviderQuery,
    IdentityProviderRead,
)
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.dependencies import CurrentUserDep

idp_router = APIRouter(prefix=IDPS_PREFIX, tags=["identity providers"])


@idp_router.options(
    "/",
    summary="List available endpoints for this resource",
    description="List available endpoints for this resource in the 'Allow' header.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def available_methods(response: Response) -> None:
    """Add the HTTP 'Allow' header to the response.

    This endpoint lists the available HTTP methods for the identity providers resource
    by adding the 'Allow' header to the response.

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
    description="Creates a new identity provider in the system. This endpoint validates"
    " the provided data, ensures no duplicate identity providers exist, and persists"
    " the new provider in the database.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Identity provider successfully created",
            "model": ItemID,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid request data",
            "model": ErrorMessage,
        },
        status.HTTP_409_CONFLICT: {
            "description": "Identity provider already exists",
            "model": ErrorMessage,
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Required fields missing or invalid",
            "model": ErrorMessage,
        },
    },
)
def create_idp(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    idp: IdentityProviderCreate,
) -> ItemID:
    """Create a new identity provider in the system.

    This endpoint creates a new identity provider with the provided data. It validates
    the input, checks for duplicates, and handles various error conditions such as
    conflicts and invalid data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (SessionDep): The database session dependency for DB operations.
        current_user (CurrentUserDep): The authenticated user creating the provider.
        idp (IdentityProviderCreate): The identity provider data to create.

    Returns:
        ItemID: A dictionary containing the ID of the created identity provider.

    Raises:
        HTTPException 409: If a provider with the same endpoint already exists.
        HTTPException 422: If required fields are missing or invalid.
        HTTPException 401: If the user is not authenticated.
        HTTPException 403: If the user does not have required permissions.

    """
    msg = f"Creating identity provider with params: {idp.model_dump_json()}"
    request.state.logger.info(msg)
    db_idp = add_idp(session=session, idp=idp, created_by=current_user)
    msg = f"Identity provider created: {db_idp.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_idp.id}


@idp_router.get(
    "/",
    summary="List all identity providers",
    description="Retrieves a paginated list of identity providers with support for"
    " filtering, sorting, and pagination. Results can be filtered by endpoint, name,"
    " groups claim, protocol, and audience.",
    responses={
        status.HTTP_200_OK: {
            "description": "List of identity providers successfully retrieved",
            "model": IdentityProviderList,
        }
    },
)
def retrieve_idps(
    request: Request,
    session: SessionDep,
    params: Annotated[IdentityProviderQuery, Query()],
) -> IdentityProviderList:
    """Retrieve a paginated list of identity providers.

    This endpoint returns a paginated list of identity providers, with support for
    filtering, sorting, and pagination through query parameters. It includes URLs for
    pagination and related resources.

    Args:
        request (Request): The HTTP request object for URL generation and logging.
        session (SessionDep): Database session dependency for DB operations.
        params (IdentityProviderQuery): Query parameters for filtering, sorting,
            and pagination.

    Returns:
        IdentityProviderList: A paginated list containing:
            - List of identity providers with their details
            - Total number of items
            - Current page number and size
            - Resource URL

    Raises:
        HTTPException 401: If the user is not authenticated.
        HTTPException 403: If the user does not have required permissions.

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
    msg += f"{[idp.model_dump_json() for idp in idps]}"
    request.state.logger.info(msg)
    new_idps = []
    for idp in idps:
        new_idp = IdentityProviderRead(
            **idp.model_dump(),  # Does not return created_by and updated_by
            created_by=idp.created_by_id,
            updated_by=idp.created_by_id,
            base_url=str(request.url),
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
    summary="Get a specific identity provider",
    description="Retrieves detailed information about a specific identity provider"
    " using its unique identifier. Returns a 404 error if the provider does not"
    " exist.",
    responses={
        status.HTTP_200_OK: {
            "description": "Identity provider successfully retrieved",
            "model": IdentityProviderRead,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Identity provider not found",
            "model": ErrorMessage,
        },
    },
)
def retrieve_idp(
    request: Request, idp: IdentityProviderRequiredDep
) -> IdentityProviderRead:
    """Retrieve a specific identity provider by ID.

    This endpoint returns detailed information about a single identity provider,
    including its endpoint, name, groups claim, protocol, and audit information.
    The existence of the identity provider is guaranteed by the dependency.

    Args:
        request (Request): The incoming HTTP request object, used for URL generation
            and logging.
        idp (IdentityProviderRequiredDep): The identity provider from the database,
            guaranteed to exist by the dependency.

    Returns:
        IdentityProviderRead: Detailed information about the identity provider,
            including all its attributes and related links.

    Raises:
        HTTPException 401: If the user is not authenticated.
        HTTPException 403: If the user lacks required permissions.
        ItemNotFoundError: If the provider doesn't exist (handled by dependency).

    """
    msg = f"Identity provider with ID '{idp.id!s}' found: {idp.model_dump_json()}"
    request.state.logger.info(msg)
    idp = IdentityProviderRead(
        **idp.model_dump(),  # Does not return created_by and updated_by
        created_by=idp.created_by_id,
        updated_by=idp.created_by_id,
        base_url=str(request.url),
    )
    return idp


@idp_router.put(
    "/{idp_id}",
    summary="Update an identity provider",
    description="Updates an existing identity provider with new data. All fields will"
    " be replaced with the provided values. Returns a 404 error if the provider"
    " doesn't exist, or a 409 if the update would create a duplicate.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Identity provider successfully updated"
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid request data",
            "model": ErrorMessage,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Identity provider not found",
            "model": ErrorMessage,
        },
        status.HTTP_409_CONFLICT: {
            "description": "Update would create a duplicate provider",
            "model": ErrorMessage,
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Required fields missing or invalid",
            "model": ErrorMessage,
        },
    },
)
def edit_idp(
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    idp_id: uuid.UUID,
    new_idp: IdentityProviderCreate,
) -> None:
    """Update an existing identity provider in the database.

    This endpoint updates all fields of an existing identity provider with new data.
    The operation validates the input data, checks for conflicts with existing
    providers, and ensures all required fields are present.

    Args:
        request (Request): The current request object, used for logging.
        session (SessionDep): The database session for DB operations.
        current_user (CurrentUserDep): The authenticated user performing the update.
        idp_id (uuid.UUID): The unique identifier of the identity provider to update.
        new_idp (IdentityProviderCreate): The new data for the identity provider.

    Raises:
        ItemNotFoundError: If the identity provider does not exist.
        ConflictError: If the update would create a duplicate provider.
        NotNullError: If required fields are missing or null.
        HTTPException 401: If the user is not authenticated.
        HTTPException 403: If the user lacks required permissions.

    """
    msg = f"Update identity provider with ID '{idp_id!s}'"
    request.state.logger.info(msg)
    update_idp(session=session, idp_id=idp_id, new_idp=new_idp, updated_by=current_user)
    msg = f"Identity provider with ID '{idp_id!s}' updated"
    request.state.logger.info(msg)


@idp_router.delete(
    "/{idp_id}",
    summary="Delete an identity provider",
    description="Removes an identity provider from the system. The operation fails if"
    " the provider has associated resources that prevent deletion.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Identity provider successfully deleted"
        },
        status.HTTP_409_CONFLICT: {
            "description": "Cannot delete provider due to existing dependencies",
            "model": ErrorMessage,
        },
    },
)
def remove_idp(request: Request, session: SessionDep, idp_id: uuid.UUID) -> None:
    """Delete an identity provider from the system.

    This endpoint permanently removes an identity provider from the system. The
    operation will fail if there are any resources (e.g., user groups) that depend
    on this provider. All dependent resources must be deleted first.

    Args:
        request (Request): The HTTP request object for logging.
        session (SessionDep): The database session for deletion operations.
        idp_id (uuid.UUID): The unique identifier of the provider to delete.

    Raises:
        DeleteFailedError: If the provider has dependent resources preventing deletion.
        HTTPException 401: If the user is not authenticated.
        HTTPException 403: If the user lacks required permissions.
        ItemNotFoundError: If the provider doesn't exist.

    Returns:
        None

    """
    msg = f"Delete identity provider with ID '{idp_id!s}'"
    request.state.logger.info(msg)
    delete_idp(session=session, idp_id=idp_id)
    msg = f"Identity provider with ID '{idp_id!s}' deleted"
    request.state.logger.info(msg)
