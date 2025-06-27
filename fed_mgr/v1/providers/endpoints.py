"""Endpoints to manage resource provider details."""

import urllib.parse
import uuid

from fastapi import APIRouter, HTTPException, Request, Response, Security, status

from fed_mgr.auth import check_authorization
from fed_mgr.db import SessionDep
from fed_mgr.exceptions import (
    ConflictError,
    NoItemToUpdateError,
    NotNullError,
    ProviderStateChangeError,
    UserNotFoundError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import IDPS_PREFIX, PROJECTS_PREFIX, PROVIDERS_PREFIX, REGIONS_PREFIX
from fed_mgr.v1.providers.crud import (
    add_provider,
    change_provider_state,
    delete_provider,
    get_providers,
    update_provider,
)
from fed_mgr.v1.providers.dependencies import ProviderDep
from fed_mgr.v1.providers.schemas import (
    ProviderCreate,
    ProviderList,
    ProviderQueryDep,
    ProviderRead,
    ProviderStatus,
    ProviderUpdate,
)
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.dependencies import CurrenUserDep

provider_router = APIRouter(
    prefix=PROVIDERS_PREFIX,
    tags=["resource providers"],
    dependencies=[Security(check_authorization)],
)


@provider_router.options(
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
    add_allow_header_to_resp(provider_router, response)


@provider_router.post(
    "/",
    summary="Create a new resource provider",
    description="Add a new resource provider to the DB. Check if a resource provider's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
    },
)
def create_provider(
    request: Request,
    session: SessionDep,
    provider: ProviderCreate,
    current_user: CurrenUserDep,
) -> ItemID:
    """Create a new resource provider in the system.

    Logs the creation attempt and result. If the resource provider already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the resource provider data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        provider (ProviderCreate | None): The resource provider data to create.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        session (SessionDep): The database session dependency.

    Returns:
        ItemID: A dictionary containing the ID of the created resource provider on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    try:
        request.state.logger.info(
            "Creating resource provider with params: %s",
            provider.model_dump(exclude_none=True),
        )
        db_provider = add_provider(
            session=session, provider=provider, created_by=current_user
        )
        request.state.logger.info("Resource Provider created: %s", repr(db_provider))
        return {"id": db_provider.id}
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
    except UserNotFoundError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e


@provider_router.get(
    "/",
    summary="Retrieve resource providers",
    description="Retrieve a paginated list of resource providers.",
)
def retrieve_providers(
    request: Request, params: ProviderQueryDep, session: SessionDep
) -> ProviderList:
    """Retrieve a paginated list of resource providers based on query parameters.

    Logs the query parameters and the number of resource providers retrieved. Fetches
    resource providers from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the resource providers in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (ProviderQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.

    Returns:
        ProviderList: A paginated list of resource providers matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    request.state.logger.info(
        "Retrieve resource providers. Query params: %s",
        params.model_dump(exclude_none=True),
    )
    providers, tot_items = get_providers(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    request.state.logger.info(
        "%d retrieved resource providers: %s", tot_items, repr(providers)
    )
    new_providers = []
    for provider in providers:
        new_provider = ProviderRead(
            **provider.model_dump(),
            links={
                "idps": urllib.parse.urljoin(
                    str(request.url), f"{provider.id}{IDPS_PREFIX}"
                ),
                "regions": urllib.parse.urljoin(
                    str(request.url), f"{provider.id}{REGIONS_PREFIX}"
                ),
                "projects": urllib.parse.urljoin(
                    str(request.url), f"{provider.id}{PROJECTS_PREFIX}"
                ),
            },
        )
        new_providers.append(new_provider)
    return ProviderList(
        data=new_providers,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@provider_router.get(
    "/{provider_id}",
    summary="Retrieve resource provider with given ID",
    description="Check if the given resource provider's ID already exists in the DB "
    "and return it. If the resource provider does not exist in the DB, the endpoint "
    "raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_provider(
    request: Request, provider_id: uuid.UUID, provider: ProviderDep
) -> ProviderRead:
    """Retrieve a resource provider by their unique identifier.

    Logs the retrieval attempt, checks if the resource provider exists, and returns the
    resource provider object if found. If the resource provider does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        provider_id (uuid.UUID): The unique identifier of the resource provider to
            retrieve.
        provider (Provider | None): The resource provider object, if found.

    Returns:
        Provider: The resource provider object if found.
        JSONResponse: A 404 response if the resource provider does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    request.state.logger.info(
        "Retrieve resource provider with ID '%s'", str(provider_id)
    )
    if provider is None:
        message = f"Resource Provider with ID '{provider_id!s}' does not exist"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    request.state.logger.info(
        "Resource Provider with ID '%s' found: %s", str(provider_id), repr(provider)
    )
    provider = ProviderRead(
        **provider.model_dump(),
        links={
            "idps": urllib.parse.urljoin(
                str(request.url), f"{provider.id}{IDPS_PREFIX}"
            ),
            "regions": urllib.parse.urljoin(
                str(request.url), f"{provider.id}{REGIONS_PREFIX}"
            ),
            "projects": urllib.parse.urljoin(
                str(request.url), f"{provider.id}{PROJECTS_PREFIX}"
            ),
        },
    )
    return provider


@provider_router.patch(
    "/{provider_id}",
    summary="Update resource provider with the given id",
    description="Update only a subset of the fields of a resource provider with the "
    "given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_provider(
    request: Request,
    provider_id: uuid.UUID,
    new_provider: ProviderUpdate,
    session: SessionDep,
    current_user: CurrenUserDep,
) -> None:
    """Update an existing resource provider in the database with the given provider ID.

    Args:
        request (Request): The current request object.
        provider_id (uuid.UUID): The unique identifier of the resource provider to
            update.
        new_provider (UserCreate): The new resource provider data to update.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.

    Raises:
        400 Bad Request: If one of the admin users does not exist in the DB (handled
            below).
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    request.state.logger.info("Update resource provider with ID '%s'", str(provider_id))
    try:
        update_provider(
            session=session,
            provider_id=provider_id,
            new_provider=new_provider,
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
    except UserNotFoundError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    request.state.logger.info(
        "Resource Provider with ID '%s' updated", str(provider_id)
    )


@provider_router.delete(
    "/{provider_id}",
    summary="Delete resource provider with given sub",
    description="Delete a resource provider with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_provider(
    request: Request, provider_id: uuid.UUID, session: SessionDep
) -> None:
    """Remove a resource provider from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_provider`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        provider_id (uuid.UUID): The unique identifier of the resource provider to be
            removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    request.state.logger.info("Delete resource provider with ID '%s'", str(provider_id))
    delete_provider(session=session, provider_id=provider_id)
    request.state.logger.info(
        "Resource Provider with ID '%s' deleted", str(provider_id)
    )


@provider_router.put(
    "/{provider_id}/change_state/{next_state}",
    summary="Change the provider state",
    description="Receive the next status the provider should go. If it is a valid one, "
    "following the status FSM, go into that state. Otherwise reject the request.",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage}},
)
def update_provider_state(
    request: Request,
    session: SessionDep,
    provider: ProviderDep,
    current_user: CurrenUserDep,
    next_state: ProviderStatus,
) -> None:
    """Change provider state.

    Update the provider state. If the next state can't be reached from the current one,
    reject the request.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (SessionDep): The database session dependency.
        provider (ProviderDep): The resource provider instance.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        next_state (ProviderStatus): Target state to reach.

    Returns:
        None

    Raises:
        400 Bad Request: If the target state is not a valid one (handled below).
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    try:
        request.state.logger.info(
            "Changing provider state from '%s' to '%s'", provider.status, next_state
        )
        change_provider_state(
            session=session,
            provider=provider,
            next_state=next_state,
            updated_by=current_user,
        )
        request.state.logger.info("Resource provider state changed")
    except ProviderStateChangeError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
