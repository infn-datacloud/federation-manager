from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    Security,
    status,
)
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from fed_mng.api.dependencies import user_exists
from fed_mng.api.utils import change_role
from fed_mng.auth import flaat, security
from fed_mng.db import get_session
from fed_mng.models import (
    Admin,
    SiteAdmin,
    SiteTester,
    SLAModerator,
    User,
    UserCreate,
    UserGroupManager,
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
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> list[User]:
    """GET operation to retrieve all users."""
    return session.exec(select(User)).all()


@router.get(
    "/admins",
    summary="Read all administrators",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
@flaat.access_level("admin")
def get_admin_list(
    request: Request,
    session: Session = Depends(get_session),
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> list[User]:
    """GET operation to retrieve all users."""
    return session.exec(select(User).join(Admin)).all()


@router.get(
    "/site_admins",
    summary="Read all site administrators",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
@flaat.access_level("admin")
def get_site_admin_list(
    request: Request,
    session: Session = Depends(get_session),
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> list[User]:
    """GET operation to retrieve all users."""
    return session.exec(select(User).join(SiteAdmin)).all()


@router.get(
    "/site_testers",
    summary="Read all site testers",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
@flaat.access_level("admin")
def get_site_tester_list(
    request: Request,
    session: Session = Depends(get_session),
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> list[User]:
    """GET operation to retrieve all users."""
    return session.exec(select(User).join(SiteTester)).all()


@router.get(
    "/sla_moderators",
    summary="Read all SLA moderators",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
@flaat.access_level("admin")
def get_sla_moderator_list(
    request: Request,
    session: Session = Depends(get_session),
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> list[User]:
    """GET operation to retrieve all users."""
    return session.exec(select(User).join(SLAModerator)).all()


@router.get(
    "/user_group_mangers",
    summary="Read all user group managers",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
@flaat.access_level("admin")
def get_user_group_mgr_list(
    request: Request,
    session: Session = Depends(get_session),
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> list[User]:
    """GET operation to retrieve all users."""
    return session.exec(select(User).join(UserGroupManager)).all()


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
    user: User = Depends(user_exists),
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
    user: User = Depends(user_exists),
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
def create_user(
    request: Request,
    user: UserCreate,
    session: Session = Depends(get_session),
    client_credentials: HTTPBasicCredentials = Security(security),
) -> User:
    """GET operation to retrieve all users."""
    try:
        user = User(**user.model_dump())
        session.add(user)
        session.commit()
        return user
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User with email `{user.email}` already exists.",
        ) from exc


@router.put(
    "/{user_id}",
    summary="Update user",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
@flaat.access_level("admin")
def udpdate_user(
    request: Request,
    user: User = Depends(user_exists),
    session: Session = Depends(get_session),
    new_data: UserUpdate = Depends(),
    is_admin: bool | None = None,
    is_site_admin: bool | None = None,
    is_site_tester: bool | None = None,
    is_sla_moderator: bool | None = None,
    is_user_group_manager: bool | None = None,
    client_credentials: HTTPBasicCredentials = Security(security),
) -> User:
    """GET operation to retrieve all users."""
    for k, v in new_data.model_dump(exclude_none=True).items():
        user.__setattr__(k, v)
    user = change_role(session, user, Admin, is_admin)
    user = change_role(session, user, SiteAdmin, is_site_admin)
    user = change_role(session, user, SiteTester, is_site_tester)
    user = change_role(session, user, SLAModerator, is_sla_moderator)
    user = change_role(session, user, UserGroupManager, is_user_group_manager)
    return user
