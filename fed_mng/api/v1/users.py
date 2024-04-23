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
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
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
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
@flaat.access_level("admin")
def get_user(
    request: Request,
    user: User = Depends(check_user_exists),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> User:
    """GET operation to retrieve all users."""
    return user


@router.delete(
    "/{user_id}",
    summary="Delete specific user",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
    status_code=status.HTTP_204_NO_CONTENT,
)
@flaat.access_level("admin")
def delete_user(
    request: Request,
    user: User = Depends(check_user_exists),
    session: Session = Depends(get_session),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> None:
    """GET operation to retrieve all users."""
    session.delete(user)
    session.commit()


@router.post(
    "/",
    summary="Create new user",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
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
    """GET operation to retrieve all users."""
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
    summary="Update user",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
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
    """GET operation to retrieve all users."""
    for k, v in new_data.model_dump(exclude_none=True).items():
        user.__setattr__(k, v)
    user = change_role(session, user, Admin, role.is_admin)
    user = change_role(session, user, SiteAdmin, role.is_site_admin)
    user = change_role(session, user, SiteTester, role.is_site_tester)
    user = change_role(session, user, SLAModerator, role.is_sla_moderator)
    user = change_role(session, user, UserGroupManager, role.is_user_group_manager)
    return user
