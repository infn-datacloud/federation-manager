"""Users endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from fed_mng.api.dependencies import check_user_exists
from fed_mng.api.utils import change_role, create_user, retrieve_users
from fed_mng.auth import flaat, security
from fed_mng.db import get_session
from fed_mng.models import (
    Admin,
    Query,
    RoleQuery,
    SiteAdmin,
    SiteTester,
    SLAModerator,
    User,
    UserCreate,
    UserGroupManager,
    UserQuery,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    summary="Read all users",
    description="""
    Retrieve all registered users with their attributes.
    If specified, results can be filtered by attribute and role. It is possible to
    paginate results (by default the endpoint returns at most 100 items). Results can
    be sorted, both ascending and descending order, by any of the user attribute.
    """,
)
@flaat.access_level("admin")
def get_user_list(
    request: Request,
    session: Session = Depends(get_session),
    item: UserQuery = Depends(),
    query: Query = Depends(),
    role: RoleQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> list[User]:
    """GET operation to retrieve all users."""
    return retrieve_users(session, item, query, role)


@router.get(
    "/{user_id}",
    summary="Read specific user",
    description="""
    Retrieve the user matching the received `user_id`. If the target item does not
    exist, raise a `404 not found` error.
    """,
)
@flaat.access_level("admin")
def get_user(
    request: Request,
    user: User = Depends(check_user_exists),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> User:
    """GET operation to retrieve a specific user."""
    return user


@router.delete(
    "/{user_id}",
    summary="Delete specific user",
    description="""
    Delete the user matching the received `user_id`. Automatically remove the associated
    roles. If the target item does not exist, raise a `404 not found` error.
    """,
    status_code=status.HTTP_204_NO_CONTENT,
)
@flaat.access_level("admin")
def delete_user(
    request: Request,
    user: User = Depends(check_user_exists),
    session: Session = Depends(get_session),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> None:
    """DELETE operation to remove a specific user."""
    session.delete(user)
    session.commit()


@router.post(
    "/",
    summary="Create new user",
    description="""Create a new user with the given attributes. During creation, it is
    possible to assign roles to the user. If an item with the same `email` already
    exists, raise a `422 validation` error.
    """,
    status_code=status.HTTP_201_CREATED,
)
@flaat.access_level("admin")
def post_user(
    request: Request,
    user: UserCreate,
    session: Session = Depends(get_session),
    role: RoleQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> User:
    """POST operation to create a user and, optionally, assign multiple roles."""
    try:
        item = create_user(session, user)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User with email `{user.email}` already exists.",
        ) from exc
    item = change_role(session, item, Admin, role.is_admin)
    item = change_role(session, item, SiteAdmin, role.is_site_admin)
    item = change_role(session, item, SiteTester, role.is_site_tester)
    item = change_role(session, item, SLAModerator, role.is_sla_moderator)
    item = change_role(session, item, UserGroupManager, role.is_user_group_manager)
    return item


@router.put(
    "/{user_id}",
    summary="Update a specific user",
    description="""
    Update the attributes of a specific user. It is possible to assign or revoke roles
    to the target user. If the target item does not exist, raise a `404 not found`
    error.
    """,
)
@flaat.access_level("admin")
def put_user(
    request: Request,
    user: User = Depends(check_user_exists),
    session: Session = Depends(get_session),
    new_data: UserUpdate = Depends(),
    role: RoleQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> User:
    """PUT operation to update a specific user."""
    for k, v in new_data.model_dump(exclude_none=True).items():
        user.__setattr__(k, v)
    user = change_role(session, user, Admin, role.is_admin)
    user = change_role(session, user, SiteAdmin, role.is_site_admin)
    user = change_role(session, user, SiteTester, role.is_site_tester)
    user = change_role(session, user, SLAModerator, role.is_sla_moderator)
    user = change_role(session, user, UserGroupManager, role.is_user_group_manager)
    return user
