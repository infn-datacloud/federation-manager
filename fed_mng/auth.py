"""Authentication and authorization rules."""
import os

import requests
from fastapi import status
from fastapi.security import HTTPBearer
from flaat.config import AccessLevel
from flaat.fastapi import Flaat
from flaat.requirements import AllOf, HasSubIss, IsTrue
from flaat.user_infos import UserInfos
from sqlmodel import Session, select

from fed_mng.config import get_settings
from fed_mng.db import engine
from fed_mng.models import (
    Admin,
    SiteAdmin,
    SiteTester,
    SLAModerator,
    User,
    UserGroupManager,
)

security = HTTPBearer()
lazy_security = HTTPBearer(auto_error=False)


def is_user(user_infos: UserInfos) -> bool:
    """Target user has write access on Federation-Registry."""
    with Session(engine) as session:
        email = user_infos.user_info.get("email")
        user = session.exec(select(User).filter(User.email == email)).first()
    return user is not None


def is_admin(user_infos: UserInfos) -> bool:
    """Target user has write access on Federation-Registry."""
    with Session(engine) as session:
        email = user_infos.user_info.get("email")
        user = session.exec(
            select(Admin).join(User).filter(User.email == email)
        ).first()
    return user is not None


def is_site_admin(user_infos: UserInfos) -> bool:
    """Target user has write access on Federation-Registry."""
    with Session(engine) as session:
        email = user_infos.user_info.get("email")
        user = session.exec(
            select(SiteAdmin).join(User).filter(User.email == email)
        ).first()
    return user is not None


def is_user_group_manager(user_infos: UserInfos) -> bool:
    """Target user has write access on Federation-Registry."""
    with Session(engine) as session:
        email = user_infos.user_info.get("email")
        user = session.exec(
            select(UserGroupManager).join(User).filter(User.email == email)
        ).first()
    return user is not None


def is_site_tester(user_infos: UserInfos) -> bool:
    """Target user has write access on Federation-Registry."""
    with Session(engine) as session:
        email = user_infos.user_info.get("email")
        user = session.exec(
            select(SiteTester).join(User).filter(User.email == email)
        ).first()
    return user is not None


def is_sla_moderator(user_infos: UserInfos) -> bool:
    """Target user has write access on Federation-Registry."""
    with Session(engine) as session:
        email = user_infos.user_info.get("email")
        user = session.exec(
            select(SLAModerator).join(User).filter(User.email == email)
        ).first()
    return user is not None


flaat = Flaat()
user_requirements = [HasSubIss(), IsTrue(is_user)]
flaat.set_access_levels(
    [
        AccessLevel("user", AllOf(*user_requirements)),
        AccessLevel("admin", AllOf(*user_requirements, IsTrue(is_admin))),
        AccessLevel("site_admin", AllOf(*user_requirements, IsTrue(is_site_admin))),
        AccessLevel("site_tester", AllOf(*user_requirements, IsTrue(is_site_tester))),
        AccessLevel("sla_mod", AllOf(*user_requirements, IsTrue(is_sla_moderator))),
        AccessLevel(
            "group_mgr", AllOf(*user_requirements, IsTrue(is_user_group_manager))
        ),
    ],
)
flaat.set_trusted_OP_list(get_settings().TRUSTED_IDP_LIST)
flaat.set_request_timeout(30)


def get_user_roles(token: str) -> list[str]:
    """Contact OPA to get user roles.

    Args:
        token (str): access token

    Raises:
        resp.raise_for_status: _description_

    Returns:
        list[str]: User roles
    """
    settings = get_settings()
    data = {"input": {"authorization": f"Bearer {token}"}}
    resp = requests.post(
        os.path.join(settings.OPA_URL, settings.ROLES_ENDPOINT), json=data
    )
    if resp.status_code == status.HTTP_200_OK:
        return resp.json().get("result", [])
    raise resp.raise_for_status()
