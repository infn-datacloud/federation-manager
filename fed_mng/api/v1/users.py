from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBasicCredentials
from sqlmodel import Session, select

from fed_mng.auth import flaat, security
from fed_mng.db import get_session
from fed_mng.models import (
    Admin,
    SLAModerator,
    SiteAdmin,
    SiteTester,
    User,
    UserGroupManager,
)
from fed_mng.workflow.manager import engine

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    summary="Read all users",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
# @flaat.access_level("user")
# @db.read_transaction
def get_user_list(
    session: Session = Depends(get_session),
    # request: Request,
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    # client_credentials: HTTPBasicCredentials = Security(security),
) -> list[User]:
    """GET operation to retrieve all users."""
    return session.exec(statement=select(Admin)).all()


@router.get(
    "/admins",
    summary="Read all administrators",
    description="Retrieve all loaded process specifications. Each returned tuple \
        contains the specification's ID, the process name and the path to the original \
        BPMN file.",
)
# @flaat.access_level("user")
# @db.read_transaction
def get_admin_list(
    session: Session = Depends(get_session),
    # request: Request,
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    # client_credentials: HTTPBasicCredentials = Security(security),
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
# @flaat.access_level("user")
# @db.read_transaction
def get_site_admin_list(
    session: Session = Depends(get_session),
    # request: Request,
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    # client_credentials: HTTPBasicCredentials = Security(security),
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
# @flaat.access_level("user")
# @db.read_transaction
def get_site_tester_list(
    session: Session = Depends(get_session),
    # request: Request,
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    # client_credentials: HTTPBasicCredentials = Security(security),
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
# @flaat.access_level("user")
# @db.read_transaction
def get_sla_moderator_list(
    session: Session = Depends(get_session),
    # request: Request,
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    # client_credentials: HTTPBasicCredentials = Security(security),
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
# @flaat.access_level("user")
# @db.read_transaction
def get_user_group_mgr_list(
    session: Session = Depends(get_session),
    # request: Request,
    # comm: DbQueryCommonParams = Depends(),
    # page: Pagination = Depends(),
    # size: SchemaSize = Depends(),
    # item: FlavorQuery = Depends(),
    # client_credentials: HTTPBasicCredentials = Security(security),
) -> list[User]:
    """GET operation to retrieve all users."""
    return session.exec(select(User).join(UserGroupManager)).all()
