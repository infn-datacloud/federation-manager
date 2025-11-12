"""Unit tests for idp dependencies in fed_mgr.v1.identity_providers.dependencies.

Covers:
- idp_required: ensures 404 is raised if parent_idp is None, otherwise does nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.identity_providers.dependencies import idp_required


def test_idp_required_success():
    """Test idp_required does nothing if parent_idp is present."""
    idp_id = uuid.uuid4()
    idp = MagicMock()  # Simulate found identity provider
    assert idp_required(idp_id, idp) == idp


def test_idp_required_not_found():
    """Test idp_required raises 404 if parent_idp is None."""
    idp_id = uuid.uuid4()
    idp = None
    with pytest.raises(
        ItemNotFoundError,
        match=f"Identity provider with ID '{idp_id!s}' does not exist",
    ):
        idp_required(idp_id, idp)
