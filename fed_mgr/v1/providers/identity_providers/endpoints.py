"""Endpoints to manage identity provider details."""

import urllib.parse
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

from fed_mgr.db import SessionDep
from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    NoItemToUpdateError,
    NotNullError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import IDPS_PREFIX, PROVIDERS_PREFIX
from fed_mgr.v1.identity_providers.dependencies import (
    IdentityProviderRequiredBodyDep,
    IdentityProviderRequiredDep,
    idp_required,
)
from fed_mgr.v1.providers.dependencies import ProviderRequiredDep, provider_required
from fed_mgr.v1.providers.identity_providers.crud import (
    connect_prov_idp,
    disconnect_prov_idp,
    get_prov_idp_links,
    update_prov_idp_link,
)
from fed_mgr.v1.providers.identity_providers.dependencies import (
    ProviderIdPConnectionDep,
)
from fed_mgr.v1.providers.identity_providers.schemas import (
    ProviderIdPConnectionCreate,
    ProviderIdPConnectionList,
    ProviderIdPConnectionQueryDep,
    ProviderIdPConnectionRead,
)
from fed_mgr.v1.schemas import ErrorMessage
from fed_mgr.v1.users.dependencies import CurrenUserDep

prov_idp_link_router = APIRouter(
    prefix=PROVIDERS_PREFIX + "/{provider_id}" + IDPS_PREFIX,
    tags=["idp overrides"],
    dependencies=[Depends(provider_required)],
)


@prov_idp_link_router.options(
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
    add_allow_header_to_resp(prov_idp_link_router, response)


@prov_idp_link_router.post(
    "/",
    summary="Connect a resource provider and an identity provider",
    description="",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
    },
)
def create_prov_idp_connection(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
    idp: IdentityProviderRequiredBodyDep,
    overrides: ProviderIdPConnectionCreate,
) -> None:
    """Create a new identity provider in the system.

    Logs the creation attempt and result. If the identity provider already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the identity provider data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        overrides (ProviderIdPConnectionCreate): Values overriding the IdP default ones.
        provider (Provider): The resource provider instance to connect.
        idp (IdentityProvider): The identity provider instance to connect.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the idp or the provider do not exist (handled below).
        409 Conflict: If the user already exists (handled below).

    """
    msg = (
        f"Connecting resource rovider with ID '{provider.id!s}' with identity provider "
    )
    msg += f"with ID '{idp.id!s}' with params: {overrides.model_dump_json()}"
    request.state.logger.info(msg)
    try:
        db_overrides = connect_prov_idp(
            session=session,
            idp=idp,
            provider=provider,
            overrides=overrides,
            created_by=current_user,
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
    msg = (
        f"Resource provider with ID '{provider.id!s}' connected with identity provider "
    )
    msg += f"with ID '{idp.id!s}' with params: {db_overrides.model_dump_json()}"
    request.state.logger.info(msg)


@prov_idp_link_router.get(
    "/",
    summary="Retrieve identity providers",
    description="Retrieve a paginated list of identity providers.",
)
def retrieve_prov_idp_connections(
    request: Request,
    session: SessionDep,
    provider_id: uuid.UUID,
    params: ProviderIdPConnectionQueryDep,
) -> ProviderIdPConnectionList:
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
        provider_id: Parent provider ID

    Returns:
        IdentityProviderList: A paginated list of identity providers matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = "Retrieve identity provider configurations details overwritten by provider "
    msg += f"with ID '{provider_id!s}'. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    links, tot_items = get_prov_idp_links(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        provider_id=provider_id,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved identity provider configurations details overwritten "
    msg += f"by provider with ID '{provider_id!s}': "
    msg += f"{[link.model_dump_json() for link in links]}"
    request.state.logger.info(msg)
    new_links = []
    for link in links:
        new_link = ProviderIdPConnectionRead(
            **link.model_dump(),  # Does not return created_by and updated_by
            created_by=link.created_by_id,
            updated_by=link.created_by_id,
            links={
                "idp": urllib.parse.urljoin(
                    str(request.base_url), f"{IDPS_PREFIX}/{link.idp_id}"
                )
            },
        )
        new_links.append(new_link)
    return ProviderIdPConnectionList(
        data=new_links,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@prov_idp_link_router.get(
    "/{idp_id}",
    summary="Retrieve identity provider with given ID",
    description="Check if the given identity provider's ID already exists in the DB "
    "and return it. If the identity provider does not exist in the DB, the endpoint "
    "raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_prov_idp_connection(
    request: Request,
    provider: ProviderRequiredDep,
    idp: IdentityProviderRequiredDep,
    overrides: ProviderIdPConnectionDep,
) -> ProviderIdPConnectionRead:
    """Retrieve a identity provider by their unique identifier.

    Logs the retrieval attempt, checks if the identity provider exists, and returns the
    identity provider object if found. If the identity provider does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        idp (uuid.UUID): The unique identifier of the identity provider to retrieve.
        provider (uuid.UUID): The unique identifier of the provider to retrieve.
        overrides (ProviderIdPConnection | None): The identity provider object, if
            found.

    Returns:
        IdentityProvider: The identity provider object if found.
        JSONResponse: A 404 response if the identity provider does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = "Retrieve configuration details for identity provider with ID "
    msg += f"'{idp.id!s}' overwritten by provider with ID '{provider.id!s}'"
    request.state.logger.info(msg)
    if overrides is None:
        msg = f"Identity Provider with ID '{idp.id!s}' is not trusted by provider "
        msg += f"with ID '{provider.id!s}'"
        request.state.logger.error(msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    msg = f"Configuration details for Identity Provider with ID '{idp.id!s}' "
    msg += f"overwritten by provider with ID '{provider.id!s}' found: {overrides!r}"
    request.state.logger.info(msg)
    overrides = ProviderIdPConnectionRead(
        **overrides.model_dump(),  # Does not return created_by and updated_by
        created_by=overrides.created_by_id,
        updated_by=overrides.created_by_id,
        links={
            "idp": urllib.parse.urljoin(
                str(request.base_url), f"{IDPS_PREFIX}/{idp.id}"
            )
        },
    )
    return overrides


@prov_idp_link_router.put(
    "/{idp_id}",
    summary="Update or create a relationship between a provider and an IdP",
    description="Update a identity provider with the given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
    dependencies=[Depends(idp_required)],
)
def edit_prov_idp_connection(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider_id: uuid.UUID,
    idp_id: uuid.UUID,
    new_overrides: ProviderIdPConnectionCreate,
) -> None:
    """Update an existing identity provider in the database with the given idp ID.

    Args:
        request (Request): The current request object.
        idp_id (uuid.UUID): The unique identifier of the identity provider to update.
        provider_id (uuid.UUID): The unique identifier of the identity provider to
            update.
        new_overrides (UserCreate): The new identity provider data to update.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.

    Raises:
        HTTPException: If the identity provider is not found or another update error
        occurs.

    """
    msg = f"Update configuration detail for identity provider with ID '{idp_id!s}' "
    msg += f"overwritten by provider with ID '{provider_id!s}'"
    request.state.logger.info(msg)
    try:
        update_prov_idp_link(
            session=session,
            idp_id=idp_id,
            provider_id=provider_id,
            new_overrides=new_overrides,
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
    msg = f"Configuration detail for identity provider with ID '{idp_id!s}' "
    msg += f"overwritten by provider with ID '{provider_id!s}' updated"
    request.state.logger.info(msg)


@prov_idp_link_router.delete(
    "/{idp_id}",
    summary="Delete identity provider with given sub",
    description="Delete a identity provider with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(idp_required)],
)
def delete_provider_idp_connection(
    request: Request,
    session: SessionDep,
    provider_id: uuid.UUID,
    idp_id: uuid.UUID,
) -> None:
    """Remove a identity provider from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_idp`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        idp_id (uuid.UUID): The unique identifier of the identity provider pointed by
            the relationship to remove
        provider_id (uuid.UUID): The unique identifier of the provider pointed by the
            relationship to remove
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Disconnect identity provider with ID '{idp_id}' from provider with ID "
    msg += f"'{provider_id}'"
    request.state.logger.info(msg)
    try:
        disconnect_prov_idp(session=session, idp_id=idp_id, provider_id=provider_id)
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Identity Provider with ID '{idp_id}' disconnected from provider with ID "
    msg += f"'{provider_id}"
    request.state.logger.info(msg)
