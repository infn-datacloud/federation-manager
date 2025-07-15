"""Unit tests for region dependencies in fed_mgr.v1.providers.regions.dependencies.

Covers:
- region_required: ensures 404 is raised if parent_region is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from fed_mgr.v1.providers.regions.dependencies import region_required


def test_region_required_success():
    """Test region_required does nothing if parent_region is present."""
    request = MagicMock()
    region_id = uuid.uuid4()
    parent_region = MagicMock()  # Simulate found region

    # Should not raise
    assert region_required(request, region_id, parent_region) is None


def test_region_required_not_found(mock_logger):
    """Test region_required raises 404 if parent_region is None."""
    request = MagicMock()
    region_id = uuid.uuid4()
    parent_region = None
    request.state.logger = mock_logger

    with pytest.raises(HTTPException) as exc:
        region_required(request, region_id, parent_region)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert f"Region with ID '{region_id!s}' does not exist" in str(exc.value.detail)
    request.state.logger.error.assert_called_once()
