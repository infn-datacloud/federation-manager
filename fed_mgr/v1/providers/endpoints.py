"""Endpoints to manage resource provider details."""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from fed_mgr.config import SettingsDep
from fed_mgr.db import SessionDep
from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    ItemNotFoundError,
    NotNullError,
    ProviderStateChangeError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import PROVIDERS_PREFIX
from fed_mgr.v1.providers.crud import (
    add_provider,
    add_site_admins,
    add_site_testers,
    change_provider_state,
    get_providers,
    remove_site_admins,
    remove_site_testers,
    revoke_provider,
    submit_provider,
    unsubmit_provider,
    update_provider,
)
from fed_mgr.v1.providers.dependencies import ProviderRequiredDep
from fed_mgr.v1.providers.schemas import (
    ProviderCreate,
    ProviderList,
    ProviderQuery,
    ProviderRead,
    ProviderStatus,
    ProviderUpdate,
)
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.dependencies import CurrenUserDep

provider_router = APIRouter(prefix=PROVIDERS_PREFIX, tags=["resource providers"])


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
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def create_provider(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    settings: SettingsDep,
    provider: ProviderCreate,
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
        settings (SettingsDep): Application ettings
        session (SessionDep): The database session dependency.

    Returns:
        ItemID: A dictionary containing the ID of the created resource provider on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Creating resource provider with params: {provider.model_dump_json()}"
    request.state.logger.info(msg)
    try:
        db_provider = add_provider(
            session=session,
            provider=provider,
            created_by=current_user,
            secret_key=settings.SECRET_KEY,
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    msg = f"Resource provider created: {db_provider.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_provider.id}


@provider_router.get(
    "/",
    summary="Retrieve resource providers",
    description="Retrieve a paginated list of resource providers.",
)
def retrieve_providers(
    request: Request, session: SessionDep, params: Annotated[ProviderQuery, Query()]
) -> ProviderList:
    """Retrieve a paginated list of resource providers based on query parameters.

    Logs the query parameters and the number of resource providers retrieved. Fetches
    resource providers from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the resource providers in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (ProviderQuery): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.

    Returns:
        ProviderList: A paginated list of resource providers matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retrieve resource providers. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    providers, tot_items = get_providers(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved resource providers: "
    msg += f"{[provider.model_dump_json() for provider in providers]}"
    request.state.logger.info(msg)
    new_providers = []
    for provider in providers:
        new_provider = ProviderRead(
            **provider.model_dump(),
            # model_dump does not return created_by, updated_by and site_admins
            created_by=provider.created_by_id,
            updated_by=provider.created_by_id,
            site_admins=[item.id for item in provider.site_admins],
            site_testers=[item.id for item in provider.site_testers],
            base_url=str(request.url),
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
def retrieve_provider(request: Request, provider: ProviderRequiredDep) -> ProviderRead:
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
    msg = f"Resource provider with ID '{provider.id!s}' found: "
    msg += f"{provider.model_dump_json()}"
    request.state.logger.info(msg)
    provider = ProviderRead(
        **provider.model_dump(),
        # model_dump does not return created_by, updated_by and  site_admins
        created_by=provider.created_by_id,
        updated_by=provider.created_by_id,
        site_admins=[item.id for item in provider.site_admins],
        site_testers=[item.id for item in provider.site_testers],
        base_url=str(request.url),
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
    session: SessionDep,
    current_user: CurrenUserDep,
    settings: SettingsDep,
    provider_id: uuid.UUID,
    new_provider: ProviderUpdate,
) -> None:
    """Update an existing resource provider in the database with the given provider ID.

    Args:
        request (Request): The current request object.
        provider_id (uuid.UUID): The unique identifier of the resource provider to
            update.
        new_provider (UserCreate): The new resource provider data to update.
        settings (SettingsDep): Application ettings
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
    msg = f"Update resource provider with ID '{provider_id!s}'"
    request.state.logger.info(msg)
    try:
        update_provider(
            session=session,
            provider_id=provider_id,
            new_provider=new_provider,
            updated_by=current_user,
            secret_key=settings.SECRET_KEY,
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
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message
        ) from e
    msg = f"Resource provider with ID '{provider_id!s}' updated"
    request.state.logger.info(msg)


@provider_router.delete(
    "/{provider_id}",
    summary="Delete resource provider",
    description="If the provider is in the draft or ready state, delete a "
    "resource provider with the given ID, from the DB. If the provider is in the "
    "active, degraded or maintenance status, change its state to deprecated. If the "
    "provider is in the deprecated state and the expiration date has been reached, or "
    "the provider is in the submitted, evaluation o pre-production state, change its "
    "state to removed.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage}},
)
def remove_provider(
    request: Request, session: SessionDep, provider_id: uuid.UUID
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
    msg = f"Delete resource provider with ID '{provider_id!s}'"
    request.state.logger.info(msg)
    try:
        revoke_provider(session=session, provider_id=provider_id)
    except (DeleteFailedError, Exception) as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Resource provider with ID '{provider_id!s}' deleted"
    request.state.logger.info(msg)


@provider_router.post(
    "/{provider_id}/testers",
    summary="Change the provider state from submitted to evaluation",
    description="Site tester assign the provied to himself.",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
    },
)
def assign_tester_to_provider(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
    tester: ItemID,
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
        users (ProviderStatus): Target state to reach.
        tester: tester id

    Returns:
        None

    Raises:
        400 Bad Request: If the target state is not a valid one (handled below).
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Assigning tester with ID '{tester.id!s}' to resource provider with "
    msg += f"ID '{provider.id!s}'"
    request.state.logger.info(msg)
    if provider.status != ProviderStatus.submitted:
        msg = f"Resource provider with ID '{provider.id!s}' is not in state "
        msg += f"'{ProviderStatus.submitted.name}' (current state: "
        msg += f"'{provider.status.name}')"
        request.state.logger.info(msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    add_site_testers(
        session=session,
        provider=provider,
        user_ids=[tester.id],
        updated_by=current_user,
    )
    msg = f"Tester with ID '{tester.id!s}' assigned to resource provider with ID "
    msg += f"'{provider.id!s}'"
    request.state.logger.info(msg)


@provider_router.delete(
    "/{provider_id}/testers/{tester_id}",
    summary="Change the provider state from submitted to evaluation",
    description="Site tester retract himself from the provider.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
    },
)
def retract_tester_from_provider(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
    tester_id: uuid.UUID,
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
        tester_id (ProviderStatus): Target state to reach.

    Returns:
        None

    Raises:
        400 Bad Request: If the target state is not a valid one (handled below).
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retract tester with ID '{tester_id!s}' from resource provider with "
    msg += f"ID '{provider.id!s}'"
    request.state.logger.info(msg)
    remove_site_testers(
        session=session,
        provider=provider,
        user_ids=[tester_id],
        updated_by=current_user,
    )
    msg = f"Tester with ID '{tester_id!s}' retracted from resource provider with "
    msg += f"ID '{provider.id!s}'"
    request.state.logger.info(msg)


@provider_router.post(
    "/{provider_id}/admins",
    summary="Change the provider state from submitted to evaluation",
    description="Site admin assign the provied to himself.",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
    },
)
def assign_admin_to_provider(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
    admin: ItemID,
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
        users (ProviderStatus): Target state to reach.
        admin: admin id

    Returns:
        None

    Raises:
        400 Bad Request: If the target state is not a valid one (handled below).
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Assigning admin with ID '{admin.id!s}' to resource provider with "
    msg += f"ID '{provider.id!s}'"
    request.state.logger.info(msg)
    add_site_admins(
        session=session,
        provider=provider,
        user_ids=[admin.id],
        updated_by=current_user,
    )
    msg = f"Admin with ID '{admin.id!s}' assigned to resource provider with ID "
    msg += f"'{provider.id!s}'"
    request.state.logger.info(msg)


@provider_router.delete(
    "/{provider_id}/admins/{admin_id}",
    summary="Change the provider state from submitted to evaluation",
    description="Site admin retract himself from the provider.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
    },
)
def retract_admin_from_provider(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
    admin_id: uuid.UUID,
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
        admin_id (ProviderStatus): Target state to reach.

    Returns:
        None

    Raises:
        400 Bad Request: If the target state is not a valid one (handled below).
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retract admin with ID '{admin_id!s}' from resource provider with "
    msg += f"ID '{provider.id!s}'"
    request.state.logger.info(msg)
    try:
        remove_site_admins(
            session=session,
            provider=provider,
            user_ids=[admin_id],
            updated_by=current_user,
        )
    except ValueError as e:
        msg = f"This is the last site admin for provider with ID '{provider.id}'"
        request.state.logger.error(msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg) from e
    msg = f"Admin with ID '{admin_id!s}' retracted from resource provider with "
    msg += f"ID '{provider.id!s}'"
    request.state.logger.info(msg)


@provider_router.post(
    "/{provider_id}/submit",
    summary="Change the provider state from ready to submit",
    description="Provider is ready to be tested. Submit federation request",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
    },
)
def submit_provider_request(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
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
    msg = f"User with ID {current_user.id!s} submitted federation request for resource "
    msg += f"provider with ID: {provider.id!s}"
    request.state.logger.info(msg)
    try:
        submit_provider(
            request=request,
            session=session,
            provider=provider,
            current_user=current_user,
        )
    except ProviderStateChangeError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Provider with ID '{provider.id!s}' state is now '{provider.status.name}'"
    request.state.logger.info(msg)


@provider_router.post(
    "/{provider_id}/unsubmit",
    summary="Change the provider state from ready to submit",
    description="Provider is ready to be tested. Submit federation request",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
    },
)
def unsubmit_provider_request(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
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
    msg = f"User with ID {current_user.id!s} revoked federation request for resource "
    msg += f"provider with ID: {provider.id!s}"
    request.state.logger.info(msg)
    try:
        unsubmit_provider(
            request=request,
            session=session,
            provider=provider,
            current_user=current_user,
        )
    except ProviderStateChangeError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Provider with ID '{provider.id!s}' state is now '{provider.status.name}'"
    request.state.logger.info(msg)


@provider_router.put(
    "/{provider_id}/change_state/{next_state}",
    summary="Change the provider state",
    description="Receive the next status the provider should go. If it is a valid one, "
    "following the status FSM, go into that state. Otherwise reject the request.",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
    },
)
def update_provider_state(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
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
    msg = f"Force provider state change of provider with ID '{provider.id!s}' from "
    msg += f"'{provider.status.name}' to '{next_state.name}'"
    request.state.logger.info(msg)
    change_provider_state(
        session=session,
        provider=provider,
        next_state=next_state,
        updated_by=current_user,
    )
    msg = f"Now, the state of resource provider with ID '{provider.id!s}' is "
    msg += f"'{provider.status.name}'"
    request.state.logger.info(msg)
