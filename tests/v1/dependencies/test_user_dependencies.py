"""Unit tests for user dependencies in fed_mgr.v1.users."""

from unittest import mock

import pytest
from fastapi import HTTPException

from fed_mgr.v1.users.dependencies import get_current_user
from fed_mgr.v1.users.schemas import User

DUMMY_SUB = "sub-123"
DUMMY_ISS = "issuer-abc"


def test_get_current_user_found(session):
    """Test get_current_user returns the user when found."""
    user_infos = mock.Mock()
    user_infos.user_info = {"sub": DUMMY_SUB, "iss": DUMMY_ISS}
    fake_user = mock.Mock(spec=User)

    def get_users(session, skip=0, limit=100, sort=None, sub=None, issuer=None):
        return [fake_user], 1

    with mock.patch(
        "fed_mgr.v1.users.dependencies.get_users", side_effect=get_users
    ) as mock_get_users:
        result = get_current_user(user_infos, session)
        mock_get_users.assert_called_once_with(
            session=session,
            skip=0,
            limit=1,
            sort="-created_at",
            sub=user_infos.user_info["sub"],
            issuer=user_infos.user_info["iss"],
        )
        assert result is fake_user


def test_get_current_user_not_found(session):
    """Test get_current_user raises HTTPException 400 when user is not found."""
    user_infos = mock.Mock()
    user_infos.user_info = {"sub": DUMMY_SUB, "iss": DUMMY_ISS}

    def get_users(session, skip=0, limit=100, sort=None, sub=None, issuer=None):
        return [], 0

    with mock.patch(
        "fed_mgr.v1.users.dependencies.get_users", side_effect=get_users
    ) as mock_get_users:
        with pytest.raises(HTTPException) as exc:
            get_current_user(user_infos, session)
        mock_get_users.assert_called_once_with(
            session=session,
            skip=0,
            limit=1,
            sort="-created_at",
            sub=user_infos.user_info["sub"],
            issuer=user_infos.user_info["iss"],
        )
        assert exc.value.status_code == 400
        assert "No user with the given credentials was found" in str(exc.value.detail)
