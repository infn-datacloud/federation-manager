"""Unit tests for user group dependencies in the identity providers module.

Covers:
- user_group_required: ensures 404 is raised if parent_idp is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.identity_providers.user_groups.dependencies import user_group_required


def test_user_group_required_success():
    """Test user_group_required does not raise when parent_user_group is provided."""
    user_group_id = uuid.uuid4()
    user_group = MagicMock()  # Simulate a found user group
    assert user_group_required(user_group_id, user_group) == user_group


def test_user_group_required_not_found():
    """Test user_group_required raises 404 and when parent_user_group is None."""
    user_group_id = uuid.uuid4()
    user_group = None
    with pytest.raises(
        ItemNotFoundError,
        match=f"User group with ID '{user_group_id!s}' does not exist",
    ):
        user_group_required(user_group_id, user_group)
