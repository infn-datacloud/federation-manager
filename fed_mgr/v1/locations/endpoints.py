"""Endpoints to manage location details."""

import uuid

from fastapi import APIRouter, HTTPException, Request, Response, Security, status

from fed_mgr.auth import check_authorization
from fed_mgr.db import SessionDep
from fed_mgr.exceptions import ConflictError, NoItemToUpdateError, NotNullError
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import LOCATIONS_PREFIX
from fed_mgr.v1.locations.crud import (
    add_location,
    delete_location,
    get_locations,
    update_location,
)
from fed_mgr.v1.locations.dependencies import LocationDep
from fed_mgr.v1.locations.schemas import (
    LocationCreate,
    LocationList,
    LocationQueryDep,
    LocationRead,
)
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.dependencies import CurrenUserDep

location_router = APIRouter(
    prefix=LOCATIONS_PREFIX,
    tags=["locations"],
    dependencies=[Security(check_authorization)],
)


@location_router.options(
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
    add_allow_header_to_resp(location_router, response)


@location_router.post(
    "/",
    summary="Create a new location",
    description="Add a new location to the DB. Check if a location with the same name "
    "already exists in the DB. If the name already exists, the endpoint raises a 409 "
    "error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
    },
)
def create_location(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    location: LocationCreate,
) -> ItemID:
    """Create a new location in the system.

    Logs the creation attempt and result. If the location already exists, returns a 409
    Conflict response.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        location (LocationCreate | None): The location data to create.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        session (SessionDep): The database session dependency.

    Returns:
        ItemID: A dictionary containing the ID of the created location on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    try:
        request.state.logger.info(
            "Creating location with params: %s", location.model_dump(exclude_none=True)
        )
        db_location = add_location(
            session=session, location=location, created_by=current_user
        )
        request.state.logger.info("Location created: %s", repr(db_location))
        return {"id": db_location.id}
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


@location_router.get(
    "/",
    summary="Retrieve locations",
    description="Retrieve a paginated list of locations.",
)
def retrieve_locations(
    request: Request, session: SessionDep, params: LocationQueryDep
) -> LocationList:
    """Retrieve a paginated list of locations based on query parameters.

    Logs the query parameters and the number of locations retrieved. Fetches
    locations from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the locations in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (LocationQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.

    Returns:
        LocationList: A paginated list of locations matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    request.state.logger.info(
        "Retrieve locations. Query params: %s", params.model_dump(exclude_none=True)
    )
    locations, tot_items = get_locations(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    request.state.logger.info("%d retrieved locations: %s", tot_items, repr(locations))
    new_locations = []
    for location in locations:
        new_locations.append(
            LocationRead(
                **location.model_dump(),  # Does not return created_by and updated_by
                created_by=location.created_by_id,
                updated_by=location.created_by_id,
            )
        )
    return LocationList(
        data=locations,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@location_router.get(
    "/{location_id}",
    summary="Retrieve location with given ID",
    description="Check if the given location's ID already exists in the DB and return "
    "it. If the location does not exist in the DB, the endpoint raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_location(
    request: Request, location_id: uuid.UUID, location: LocationDep
) -> LocationRead:
    """Retrieve a location by their unique identifier.

    Logs the retrieval attempt, checks if the location exists, and returns the
    location object if found. If the location does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        location_id (uuid.UUID): The unique identifier of the location to retrieve.
        location (Location | None): The location object, if found.

    Returns:
        Location: The location object if found.
        JSONResponse: A 404 response if the location does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    request.state.logger.info("Retrieve location with ID '%s'", str(location_id))
    if location is None:
        message = f"Location with ID '{location_id!s}' does not exist"
        request.state.logger.error(message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    request.state.logger.info(
        "Location with ID '%s' found: %s", str(location_id), repr(location)
    )
    location = LocationRead(
        **location.model_dump(),  # Does not return created_by and updated_by
        created_by=location.created_by_id,
        updated_by=location.created_by_id,
    )
    return location


@location_router.put(
    "/{location_id}",
    summary="Update location with the given ID",
    description="Update a location with the given ID in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_location(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    location_id: uuid.UUID,
    new_location: LocationCreate,
) -> None:
    """Update an existing location in the database with the given location ID.

    Args:
        request (Request): The current request object.
        location_id (uuid.UUID): The unique identifier of the location to update.
        new_location (UserCreate): The new location data to update.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.

    Raises:
        HTTPException: If the location is not found or another update error
        occurs.

    """
    request.state.logger.info("Update location with ID '%s'", str(location_id))
    try:
        update_location(
            session=session,
            location_id=location_id,
            new_location=new_location,
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
    request.state.logger.info("Location with ID '%s' updated", str(location_id))


@location_router.delete(
    "/{location_id}",
    summary="Delete location with given sub",
    description="Delete a location with the given ID from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_location(
    request: Request, session: SessionDep, location_id: uuid.UUID
) -> None:
    """Remove a location from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_location`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        location_id (uuid.UUID): The unique identifier of the location to be removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    request.state.logger.info("Delete location with ID '%s'", str(location_id))
    delete_location(session=session, location_id=location_id)
    request.state.logger.info("Location with ID '%s' deleted", str(location_id))
