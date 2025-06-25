"""Unit tests for idp dependencies in fed_mgr.v1.identity_providers.dependencies.

Covers:
- idp_required: ensures 404 is raised if parent_idp is None, otherwise does nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from fed_mgr.v1.identity_providers.dependencies import idp_required


def test_idp_required_success():
    """Test idp_required does nothing if parent_idp is present."""
    request = MagicMock()
    idp_id = uuid.uuid4()
    parent_idp = MagicMock()  # Simulate found identity provider

    # Should not raise
    assert idp_required(request, idp_id, parent_idp) is None


def test_idp_required_not_found(mock_logger):
    """Test idp_required raises 404 if parent_idp is None."""
    request = MagicMock()
    idp_id = uuid.uuid4()
    parent_idp = None
    request.state.logger = mock_logger

    with pytest.raises(HTTPException) as exc:
        idp_required(request, idp_id, parent_idp)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert f"Identity Provider with ID '{idp_id!s}' does not exist" in str(
        exc.value.detail
    )
    request.state.logger.error.assert_called_once()
