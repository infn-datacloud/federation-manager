"""Unit tests for user dependencies in fed_mgr.v1.users."""

from unittest import mock

import pytest
from fastapi import HTTPException

from fed_mgr.v1.models import User
from fed_mgr.v1.users.dependencies import get_current_user

DUMMY_SUB = "sub-123"
DUMMY_ISS = "issuer-abc"


def test_get_current_user_found(session):
    """Test get_current_user returns the user when found."""
    user_infos = mock.Mock()
    user_infos.user_info = {"sub": DUMMY_SUB, "iss": DUMMY_ISS}
    fake_user = mock.Mock(spec=User)

    def get_user(session, sub=None, issuer=None):
        return fake_user

    with mock.patch(
        "fed_mgr.v1.users.dependencies.get_user", side_effect=get_user
    ) as mock_get_user:
        result = get_current_user(user_infos, session)
        mock_get_user.assert_called_once_with(
            session=session,
            sub=user_infos.user_info["sub"],
            issuer=user_infos.user_info["iss"],
        )
        assert result is fake_user


def test_get_current_user_not_found(session):
    """Test get_current_user raises HTTPException 400 when user is not found."""
    user_infos = mock.Mock()
    user_infos.user_info = {"sub": DUMMY_SUB, "iss": DUMMY_ISS}

    with mock.patch(
        "fed_mgr.v1.users.dependencies.get_user", return_value=None
    ) as mock_get_user:
        with pytest.raises(HTTPException) as exc:
            get_current_user(user_infos, session)
        mock_get_user.assert_called_once_with(
            session=session,
            sub=user_infos.user_info["sub"],
            issuer=user_infos.user_info["iss"],
        )
        assert exc.value.status_code == 400
        assert "No user with the given credentials was found" in str(exc.value.detail)
