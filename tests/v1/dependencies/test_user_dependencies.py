"""Unit tests for user dependencies in fed_mgr.v1.users."""

import uuid
from unittest.mock import MagicMock, patch

import flaat
import pytest

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.models import User
from fed_mgr.v1.users.dependencies import get_current_user, user_required

DUMMY_SUB = "sub-123"
DUMMY_ISS = "issuer-abc"


def test_user_required_success():
    """Test user_required does nothing if parent_user is present."""
    user_id = uuid.uuid4()
    user = MagicMock()  # Simulate found user
    current_user = MagicMock()  # Simulate current user

    assert user_required(user_id, current_user, user) == user
    assert user_required("me", current_user, user) == current_user
    assert user_required("me", current_user, None) == current_user


def test_user_required_not_found():
    """Test user_required raises 404 if parent_user is None."""
    user_id = uuid.uuid4()
    user = None
    current_user = MagicMock()  # Simulate current user
    with pytest.raises(
        ItemNotFoundError, match=f"User with ID '{user_id!s}' does not exist"
    ):
        user_required(user_id, current_user, user)


def test_get_current_user_found(session):
    """Test get_current_user returns the user when found."""
    user_infos = MagicMock(spec=flaat.UserInfos)
    user_infos.user_info = {"sub": DUMMY_SUB, "iss": DUMMY_ISS}
    fake_user = MagicMock(spec=User)

    with patch(
        "fed_mgr.v1.users.dependencies.get_users", return_value=([fake_user], 1)
    ) as mock_get_user:
        result = get_current_user(user_infos, session)
        mock_get_user.assert_called_once_with(
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
    user_infos = MagicMock()
    user_infos.user_info = {"sub": DUMMY_SUB, "iss": DUMMY_ISS}

    with patch(
        "fed_mgr.v1.users.dependencies.get_users", return_value=([], 0)
    ) as mock_get_user:
        with pytest.raises(
            ItemNotFoundError, match="No user with the given credentials was found"
        ):
            get_current_user(user_infos, session)
        mock_get_user.assert_called_once_with(
            session=session,
            skip=0,
            limit=1,
            sort="-created_at",
            sub=user_infos.user_info["sub"],
            issuer=user_infos.user_info["iss"],
        )
