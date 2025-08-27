"""Unit tests for user group dependencies in the identity providers module.

Covers:
- user_group_required: ensures 404 is raised if parent_idp is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from fed_mgr.v1.identity_providers.user_groups.dependencies import user_group_required


def test_user_group_required_success():
    """Test user_group_required does not raise when parent_user_group is provided."""
    request = MagicMock()
    idp_id = uuid.uuid4()
    parent_user_group = MagicMock()  # Simulate a found user group

    # Should not raise
    assert user_group_required(request, idp_id, parent_user_group) == parent_user_group


def test_user_group_required_not_found(mock_logger):
    """Test user_group_required raises 404 and when parent_user_group is None."""
    request = MagicMock()
    user_group_id = uuid.uuid4()
    parent_user_group = None
    request.state.logger = mock_logger

    with pytest.raises(HTTPException) as exc:
        user_group_required(request, user_group_id, parent_user_group)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert f"User group with ID '{user_group_id!s}' does not exist" in exc.value.detail
    request.state.logger.error.assert_called_once()
