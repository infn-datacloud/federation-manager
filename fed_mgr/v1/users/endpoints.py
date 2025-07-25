"""Endpoints to manage User details."""

import uuid

from fastapi import APIRouter, HTTPException, Request, Response, Security, status

from fed_mgr.auth import AuthenticationDep, check_authorization
from fed_mgr.db import SessionDep
from fed_mgr.exceptions import (
    ConflictError,
    DeleteFailedError,
    NoItemToUpdateError,
    NotNullError,
)
from fed_mgr.utils import add_allow_header_to_resp
from fed_mgr.v1 import USERS_PREFIX
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.crud import add_user, delete_user, get_users, update_user
from fed_mgr.v1.users.dependencies import UserDep
from fed_mgr.v1.users.schemas import UserCreate, UserList, UserQueryDep, UserRead

user_router = APIRouter(
    prefix=USERS_PREFIX,
    tags=["users"],
    dependencies=[Security(check_authorization)],
)


@user_router.options(
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
    add_allow_header_to_resp(user_router, response)


@user_router.post(
    "/",
    summary="Create a new user",
    description="Add a new user to the DB. Check if a user's subject, for this issuer, "
    "already exists in the DB. If the sub already exists, the endpoint raises a 409 "
    "error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def create_user(
    request: Request, session: SessionDep, current_user_infos: AuthenticationDep
) -> ItemID:
    """Create a new user in the system.

    Logs the creation attempt and result. If the user already exists, returns a 409
    Conflict response. If no body is given, it retrieves from the access token the user
    data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        user (UserCreate | None): The user data to create.
        current_user_infos (AuthenticationDep): The authentication information of the
            current user retrieved from the access token.
        session (SessionDep): The database session dependency.

    Returns:
        ItemID: A dictionary containing the ID of the created user on success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        409 Conflict: If the user already exists (handled below).

    """
    user = UserCreate(
        sub=current_user_infos.subject,
        issuer=current_user_infos.issuer,
        name=current_user_infos.user_info["name"],
        email=current_user_infos.user_info["email"],
    )
    msg = f"Creating user with params: {user.model_dump_json()}"
    request.state.logger.info(msg)
    try:
        db_user = add_user(session=session, user=user)
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
    msg = f"User created: {db_user.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_user.id}


@user_router.get(
    "/",
    summary="Retrieve users",
    description="Retrieve a paginated list of users.",
)
def retrieve_users(
    request: Request, session: SessionDep, params: UserQueryDep
) -> UserList:
    """Retrieve a paginated list of users based on query parameters.

    Logs the query parameters and the number of users retrieved. Fetches users from the
    database using pagination, sorting, and additional filters provided in the query
    parameters. Returns the users in a paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (UserQueryDep): Dependency containing query parameters for filtering,
            sorting, and pagination.
        session (SessionDep): Database session dependency.

    Returns:
        UserList: A paginated list of users matching the query parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Retrieve users. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    users, tot_items = get_users(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved users: {[user.model_dump_json() for user in users]}"
    request.state.logger.info(msg)
    return UserList(
        data=users,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@user_router.get(
    "/{user_id}",
    summary="Retrieve user with given ID",
    description="Check if the given user's ID already exists in the DB and return it. "
    "If the user does not exist in the DB, the endpoint raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_user(request: Request, user_id: uuid.UUID, user: UserDep) -> UserRead:
    """Retrieve a user by their unique identifier.

    Logs the retrieval attempt, checks if the user exists, and returns the user object
    if found. If the user does not exist, logs an error and returns a JSON response with
    a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        user_id (uuid.UUID): The unique identifier of the user to retrieve.
        user (User | None): The user object, if found.

    Returns:
        User: The user object if found.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = f"Retrieve user with ID '{user_id!s}'"
    request.state.logger.info(msg)
    if user is None:
        msg = f"User with ID '{user_id!s}' does not exist"
        request.state.logger.error(msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    msg = f"User with ID '{user_id!s}' found: {user.model_dump_json()}"
    request.state.logger.info(msg)
    return user


@user_router.put(
    "/{user_id}",
    summary="Update user with the given id",
    description="Update a user with the given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_user(
    request: Request,
    session: SessionDep,
    user_id: uuid.UUID,
    new_user: UserCreate,
) -> None:
    """Update an existing user in the database with the given user ID.

    Args:
        request (Request): The current request object.
        user_id (uuid.UUID): The unique identifier of the user to update.
        new_user (UserCreate): The new user data to update.
        session (SessionDep): The database session dependency.

    Raises:
        HTTPException: If the user is not found or another update error occurs.

    """
    msg = f"Update user with ID '{user_id!s}'"
    request.state.logger.info(msg)
    try:
        update_user(session=session, user_id=user_id, new_user=new_user)
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
    msg = f"User with ID '{user_id!s}' updated"
    request.state.logger.info(msg)


@user_router.delete(
    "/{user_id}",
    summary="Delete user with given id",
    description="Delete a user with the given id from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user(request: Request, session: SessionDep, user_id: uuid.UUID) -> None:
    """Remove a user from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the `delete_user`
    function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        user_id (uuid.UUID): The unique identifier of the user to be removed.
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).

    """
    msg = f"Delete user with ID '{user_id!s}'"
    request.state.logger.info(msg)
    try:
        delete_user(session=session, user_id=user_id)
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"User with ID '{user_id!s}' deleted"
    request.state.logger.info(msg)
