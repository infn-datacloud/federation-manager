from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import HTTPBasicCredentials
from sqlmodel import Session, select

from fed_mng.auth import flaat, security
from fed_mng.db import get_session
from fed_mng.models import User
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
    return session.exec(select(User)).all()
