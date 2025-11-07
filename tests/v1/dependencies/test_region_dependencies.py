"""Unit tests for region dependencies in fed_mgr.v1.providers.regions.dependencies.

Covers:
- region_required: ensures 404 is raised if region is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.providers.regions.dependencies import region_required


def test_region_required_success():
    """Test region_required does nothing if region is present."""
    region_id = uuid.uuid4()
    region = MagicMock()  # Simulate found region
    # Should not raise
    assert region_required(region_id, region) == region


def test_region_required_not_found():
    """Test region_required raises 404 if region is None."""
    region_id = uuid.uuid4()
    region = None
    with pytest.raises(
        ItemNotFoundError, match=f"Region with ID '{region_id!s}' does not exist"
    ):
        region_required(region_id, region)
