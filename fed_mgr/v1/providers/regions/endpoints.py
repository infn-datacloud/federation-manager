"""Endpoints to manage region details."""

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
    ItemNotFoundError,
    NotNullError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import PROVIDERS_PREFIX, REGIONS_PREFIX
from fed_mgr.v1.providers.dependencies import (
    ProviderRequiredDep,
    provider_required,
)
from fed_mgr.v1.providers.regions.crud import (
    add_region,
    delete_region,
    get_regions,
    update_region,
)
from fed_mgr.v1.providers.regions.dependencies import RegionRequiredDep
from fed_mgr.v1.providers.regions.schemas import (
    RegionCreate,
    RegionList,
    RegionQueryDep,
    RegionRead,
)
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.dependencies import CurrenUserDep

region_router = APIRouter(
    prefix=PROVIDERS_PREFIX + "/{provider_id}" + REGIONS_PREFIX,
    tags=["regions"],
    dependencies=[Depends(provider_required)],
)


@region_router.options(
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
    add_allow_header_to_resp(region_router, response)


@region_router.post(
    "/",
    summary="Create a new region",
    description="Add a new region to the DB. Check if a resource region's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
    },
)
def create_region(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    provider: ProviderRequiredDep,
    region: RegionCreate,
) -> ItemID:
    """Create a new resource region in the system.

    Logs the creation attempt and result. If the resource region already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the resource region data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        region (RegionCreate | None): The resource region data to create.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        session (SessionDep): The database session dependency.
        provider (Provider): The region's parent provider.

    Returns:
        ItemID: A dictionary containing the ID of the created resource region on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Creating region with params: {region.model_dump_json()}"
    request.state.logger.info(msg)
    try:
        db_region = add_region(
            session=session, region=region, created_by=current_user, provider=provider
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
    # except LocationNotFoundError as e:
    #     request.state.logger.error(e.message)
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
    #     ) from e
    msg = f"Region created: {db_region.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_region.id}


@region_router.get(
    "/",
    summary="Retrieve regions",
    description="Retrieve a paginated list of regions.",
)
def retrieve_regions(
    request: Request,
    session: SessionDep,
    provider: ProviderRequiredDep,
    params: RegionQueryDep,
) -> RegionList:
    """Retrieve a paginated list of regions based on query parameters.

    Logs the query parameters and the number of resource regions retrieved. Fetches
    resource regions from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the resource regions in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (RegionQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.
        provider: Parent provider ID

    Returns:
        RegionList: A paginated list of resource regions matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retrieve regions. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    regions, tot_items = get_regions(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        provider_id=provider.id,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved regions: "
    msg += f"{[region.model_dump_json() for region in regions]}"
    request.state.logger.info(msg)
    new_regions = []
    for region in regions:
        new_region = RegionRead(
            **region.model_dump(),  # Does not return created_by and updated_by
            created_by=region.created_by_id,
            updated_by=region.created_by_id,
            # links={
            #     "location": urllib.parse.urljoin(
            #         str(request.url),
            #         f"{region.id}{LOCATIONS_PREFIX}/{region.location_id}",
            #     ),
            # },
        )
        new_regions.append(new_region)
    return RegionList(
        data=new_regions,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@region_router.get(
    "/{region_id}",
    summary="Retrieve resource region with given ID",
    description="Check if the given resource region's ID already exists in the DB "
    "and return it. If the resource region does not exist in the DB, the endpoint "
    "raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_region(request: Request, region: RegionRequiredDep) -> RegionRead:
    """Retrieve a resource region by their unique identifier.

    Logs the retrieval attempt, checks if the resource region exists, and returns the
    resource region object if found. If the resource region does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        region_id (uuid.UUID): The unique identifier of the resource region to
            retrieve.
        region (Region | None): The resource region object, if found.

    Returns:
        Region: The resource region object if found.
        JSONResponse: A 404 response if the resource region does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = f"Region with ID '{region.id!s}' found: {region.model_dump_json()}"
    request.state.logger.info(msg)
    region = RegionRead(
        **region.model_dump(),  # Does not return created_by and updated_by
        created_by=region.created_by_id,
        updated_by=region.created_by_id,
        # links={
        #     "location": urllib.parse.urljoin(
        #         str(request.url),
        #         f"{region.id}{LOCATIONS_PREFIX}/{region.location_id}",
        #     ),
        # },
    )
    return region


@region_router.put(
    "/{region_id}",
    summary="Update resource region with the given id",
    description="Update only a subset of the fields of a resource region with the "
    "given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_region(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    region_id: uuid.UUID,
    new_region: RegionCreate,
) -> None:
    """Update an existing resource region in the database with the given region ID.

    Args:
        request (Request): The current request object.
        region_id (uuid.UUID): The unique identifier of the resource region to
            update.
        new_region (UserCreate): The new resource region data to update.
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
    msg = f"Update region with ID '{region_id!s}'"
    request.state.logger.info(msg)
    try:
        update_region(
            session=session,
            region_id=region_id,
            new_region=new_region,
            updated_by=current_user,
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
    # except LocationNotFoundError as e:
    #     request.state.logger.error(e.message)
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
    #     ) from e
    msg = f"Region with ID '{region_id!s}' updated"
    request.state.logger.info(msg)


@region_router.delete(
    "/{region_id}",
    summary="Delete resource region with given sub",
    description="Delete a resource region with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_region(request: Request, session: SessionDep, region_id: uuid.UUID) -> None:
    """Remove a resource region from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_region`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        region_id (uuid.UUID): The unique identifier of the resource region to be
            removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Delete region with ID '{region_id!s}'"
    request.state.logger.info(msg)
    try:
        delete_region(session=session, region_id=region_id)
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"Region with ID '{region_id!s}' deleted"
    request.state.logger.info(msg)
