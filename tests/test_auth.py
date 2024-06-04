from unittest.mock import MagicMock, patch

from fastapi import status
from flaat import UserInfos
from pytest_cases import parametrize_with_cases
from sqlmodel import Session, select

from fed_mng.auth import (
    get_user_roles,
    is_admin,
    is_site_admin,
    is_site_tester,
    is_sla_moderator,
    is_user_group_manager,
)
from fed_mng.models import (
    Admin,
    SiteAdmin,
    SiteTester,
    SLAModerator,
    User,
    UserGroupManager,
)
from tests.utils import random_email


def test_is_admin(db_session: Session, db_admin: Admin) -> None:
    user: User = db_session.exec(select(User).filter(User.id == db_admin.id)).first()
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": user.email},
        introspection_info=None,
    )
    assert is_admin(user_info)


def test_is_not_admin() -> None:
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": random_email()},
        introspection_info=None,
    )
    assert not is_admin(user_info)


def test_is_site_admin(db_session: Session, db_site_admin: SiteAdmin) -> None:
    user: User = db_session.exec(
        select(User).filter(User.id == db_site_admin.id)
    ).first()
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": user.email},
        introspection_info=None,
    )
    assert is_site_admin(user_info)


def test_is_not_site_admin() -> None:
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": random_email()},
        introspection_info=None,
    )
    assert not is_site_admin(user_info)


def test_is_site_tester(db_session: Session, db_site_tester: SiteTester) -> None:
    user: User = db_session.exec(
        select(User).filter(User.id == db_site_tester.id)
    ).first()
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": user.email},
        introspection_info=None,
    )
    assert is_site_tester(user_info)


def test_is_not_site_tester() -> None:
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": random_email()},
        introspection_info=None,
    )
    assert not is_site_tester(user_info)


def test_is_sla_moderator(db_session: Session, db_sla_moderator: SLAModerator) -> None:
    user: User = db_session.exec(
        select(User).filter(User.id == db_sla_moderator.id)
    ).first()
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": user.email},
        introspection_info=None,
    )
    assert is_sla_moderator(user_info)


def test_is_not_sla_moderator() -> None:
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": random_email()},
        introspection_info=None,
    )
    assert not is_sla_moderator(user_info)


def test_is_user_group_manager(
    db_session: Session, db_user_group_manager: UserGroupManager
) -> None:
    user: User = db_session.exec(
        select(User).filter(User.id == db_user_group_manager.id)
    ).first()
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": user.email},
        introspection_info=None,
    )
    assert is_user_group_manager(user_info)


def test_is_not_user_group_manager() -> None:
    user_info = UserInfos(
        access_token_info=None,
        user_info={"email": random_email()},
        introspection_info=None,
    )
    assert not is_user_group_manager(user_info)


@patch("fed_mng.auth.requests")
@parametrize_with_cases("opa_resp", has_tag="valid")
def test_opa_auth(mock_requests: MagicMock, opa_resp: list[str]) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = status.HTTP_200_OK
    mock_resp.json.return_value = opa_resp
    mock_requests.post.return_value = mock_resp
    user_roles = get_user_roles("fake_token")
    assert user_roles is not None
    assert isinstance(user_roles, list)
    assert len(user_roles) == len(opa_resp.get("result", []))


@patch("fed_mng.auth.requests")
@parametrize_with_cases("status_code", has_tag="http_exc")
def test_opa_auth_http_exc(mock_requests: MagicMock, status_code: int) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_requests.post.return_value = mock_resp
    user_roles = get_user_roles("fake_token")
    assert user_roles is not None
    assert isinstance(user_roles, list)
    assert len(user_roles) == 0


@patch("fed_mng.auth.requests")
@parametrize_with_cases("err", has_tag="conn_err")
def test_opa_auth_conn_err(mock_requests: MagicMock, err) -> None:
    mock_requests.post.side_effect = err()
    user_roles = get_user_roles("fake_token")
    assert user_roles is not None
    assert isinstance(user_roles, list)
    assert len(user_roles) == 0
