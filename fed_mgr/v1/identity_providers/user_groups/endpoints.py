"""Endpoints to manage user group details."""

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
from fed_mgr.v1 import IDPS_PREFIX, USER_GROUPS_PREFIX
from fed_mgr.v1.identity_providers.dependencies import (
    IdentityProviderRequiredDep,
    idp_required,
)
from fed_mgr.v1.identity_providers.user_groups.crud import (
    add_user_group,
    delete_user_group,
    get_user_groups,
    update_user_group,
)
from fed_mgr.v1.identity_providers.user_groups.dependencies import UserGroupRequiredDep
from fed_mgr.v1.identity_providers.user_groups.schemas import (
    UserGroupCreate,
    UserGroupList,
    UserGroupQueryDep,
    UserGroupRead,
)
from fed_mgr.v1.schemas import ErrorMessage, ItemID
from fed_mgr.v1.users.dependencies import CurrenUserDep

user_group_router = APIRouter(
    prefix=IDPS_PREFIX + "/{idp_id}" + USER_GROUPS_PREFIX,
    tags=["user groups"],
    dependencies=[Depends(idp_required)],
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)


@user_group_router.options(
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
        404 Not Found: If the parent identity provider does not exists.

    """
    add_allow_header_to_resp(user_group_router, response)


@user_group_router.post(
    "/",
    summary="Create a new user group",
    description="Add a new user group to the DB. Check if a user group's "
    "subject, for this issuer, already exists in the DB. If the sub already exists, "
    "the endpoint raises a 409 error.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorMessage},
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
    },
)
def create_user_group(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    idp: IdentityProviderRequiredDep,
    user_group: UserGroupCreate,
) -> ItemID:
    """Create a new user group in the system.

    Logs the creation attempt and result. If the user group already exists,
    returns a 409 Conflict response. If no body is given, it retrieves from the access
    token the user group data.

    Args:
        request (Request): The incoming HTTP request object, used for logging.
        session (SessionDep): The database session dependency.
        user_group (UserGroupCreate | None): The user group data to create.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.
        idp (IdentityProvider): The parent identity provider's ID.

    Returns:
        ItemID: A dictionary containing the ID of the created user group on
        success.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the parent identity provider does not exists.
        409 Conflict: If the user already exists (handled below).

    """
    msg = f"Creating user group with params: {user_group.model_dump_json()}"
    request.state.logger.info(msg)
    try:
        db_user_group = add_user_group(
            session=session, user_group=user_group, created_by=current_user, idp=idp
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
    msg = f"User group created: {db_user_group.model_dump_json()}"
    request.state.logger.info(msg)
    return {"id": db_user_group.id}


@user_group_router.get(
    "/",
    summary="Retrieve user groups",
    description="Retrieve a paginated list of user groups.",
)
def retrieve_user_groups(
    request: Request,
    session: SessionDep,
    idp: IdentityProviderRequiredDep,
    params: UserGroupQueryDep,
) -> UserGroupList:
    """Retrieve a paginated list of user groups based on query parameters.

    Logs the query parameters and the number of user groups retrieved. Fetches
    user groups from the database using pagination, sorting, and additional
    filters provided in the query parameters. Returns the user groups in a
    paginated response format.

    Args:
        request (Request): The HTTP request object, used for logging and URL generation.
        params (UserGroupQueryDep): Dependency containing query parameters for
            filtering, sorting, and pagination.
        session (SessionDep): Database session dependency.
        idp: Parent identity Provider ID

    Returns:
        UserGroupList: A paginated list of user groups matching the query
            parameters.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the parent identity provider does not exists.

    """
    msg = f"Retrieve user groups. Query params: {params.model_dump_json()}"
    request.state.logger.info(msg)
    user_groups, tot_items = get_user_groups(
        session=session,
        skip=(params.page - 1) * params.size,
        limit=params.size,
        sort=params.sort,
        idp_id=idp.id,
        **params.model_dump(exclude={"page", "size", "sort"}, exclude_none=True),
    )
    msg = f"{tot_items} retrieved user groups: "
    msg += f"{[group.model_dump_json() for group in user_groups]}"
    request.state.logger.info(msg)
    new_user_groups = []
    for user_group in user_groups:
        new_user_group = UserGroupRead(
            **user_group.model_dump(),  # Does not return created_by and updated_by
            created_by=user_group.created_by_id,
            updated_by=user_group.created_by_id,
            base_url=str(request.url),
        )
        new_user_groups.append(new_user_group)
    return UserGroupList(
        data=new_user_groups,
        resource_url=str(request.url),
        page_number=params.page,
        page_size=params.size,
        tot_items=tot_items,
    )


@user_group_router.get(
    "/{user_group_id}",
    summary="Retrieve user group with given ID",
    description="Check if the given user group's ID already exists in the DB "
    "and return it. If the user group does not exist in the DB, the endpoint "
    "raises a 404 error.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorMessage}},
)
def retrieve_user_group(
    request: Request, user_group: UserGroupRequiredDep
) -> UserGroupRead:
    """Retrieve a user group by their unique identifier.

    Logs the retrieval attempt, checks if the user group exists, and returns the
    user group object if found. If the user group does not exist, logs an
    error and returns a JSON response with a 404 status.

    Args:
        request (Request): The incoming HTTP request object.
        user_group_id (uuid.UUID): The unique identifier of the user group to retrieve.
        user_group (UserGroup | None): The user group object, if found.

    Returns:
        UserGroup: The user group object if found.
        JSONResponse: A 404 response if the user group does not exist.

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the user does not exist (handled below).

    """
    msg = f"User group with ID '{user_group.id!s}' found: "
    msg += f"{user_group.model_dump_json()}"
    request.state.logger.info(msg)
    user_group = UserGroupRead(
        **user_group.model_dump(),  # Does not return created_by and updated_by
        created_by=user_group.created_by_id,
        updated_by=user_group.created_by_id,
        base_url=str(request.url),
    )
    return user_group


@user_group_router.put(
    "/{user_group_id}",
    summary="Update user group with the given id",
    description="Update a user group with the given id in the DB",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_409_CONFLICT: {"model": ErrorMessage},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorMessage},
    },
)
def edit_user_group(
    request: Request,
    session: SessionDep,
    current_user: CurrenUserDep,
    user_group_id: uuid.UUID,
    new_user_group: UserGroupCreate,
) -> None:
    """Update an existing user group in the database with the given user_group ID.

    Args:
        request (Request): The current request object.
        user_group_id (uuid.UUID): The unique identifier of the user group to update.
        new_user_group (UserCreate): The new user group data to update.
        session (SessionDep): The database session dependency.
        current_user (CurrenUserDep): The DB user matching the current user retrieved
            from the access token.

    Raises:
        404 Not Found: If the parent identity provider does not exists, if the user
            group is not found

    """
    msg = f"Update user group with ID '{user_group_id!s}'"
    request.state.logger.info(msg)
    try:
        update_user_group(
            session=session,
            user_group_id=user_group_id,
            new_user_group=new_user_group,
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
    msg = f"User group with ID '{user_group_id!s}' updated"
    request.state.logger.info(msg)


@user_group_router.delete(
    "/{user_group_id}",
    summary="Delete user group with given sub",
    description="Delete a user group with the given subject, for this issuer, "
    "from the DB.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user_group(
    request: Request, session: SessionDep, user_group_id: uuid.UUID
) -> None:
    """Remove a user group from the system by their unique identifier.

    Logs the deletion process and delegates the actual removal to the
    `delete_user_group` function.

    Args:
        request (Request): The HTTP request object, used for logging and request context
        user_group_id (uuid.UUID): The unique identifier of the user group to be removed
        session (SessionDep): The database session dependency used to perform the
            deletion.

    Returns:
        None

    Raises:
        401 Unauthorized: If the user is not authenticated (handled by dependencies).
        403 Forbidden: If the user does not have permission (handled by dependencies).
        404 Not Found: If the parent identity provider does not exists.

    """
    msg = f"Delete user group with ID '{user_group_id!s}'"
    request.state.logger.info(msg)
    try:
        delete_user_group(session=session, user_group_id=user_group_id)
    except DeleteFailedError as e:
        request.state.logger.error(e.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        ) from e
    msg = f"User group with ID '{user_group_id!s}' deleted"
    request.state.logger.info(msg)
