"""Unit tests for project dependencies in fed_mgr.v1.providers.projects.dependencies.

Covers:
- project_required: ensures 404 is raised if parent_project is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.providers.projects.regions.dependencies import region_overrides_required


def test_reg_overrides_required_success():
    """Test project_required does nothing if parent_project is present."""
    project_id = uuid.uuid4()
    region_id = uuid.uuid4()
    overrides = MagicMock()  # Simulate found resource project
    # Should not raise
    assert region_overrides_required(project_id, region_id, overrides) == overrides


def test_reg_overrides_required_not_found():
    """Test project_required raises 404 if parent_project is None."""
    project_id = uuid.uuid4()
    region_id = uuid.uuid4()
    overrides = None

    message = f"Project with ID '{project_id!s}' does not define overrides for "
    message += f"region with ID '{region_id!s}'"
    with pytest.raises(ItemNotFoundError, match=message):
        region_overrides_required(project_id, region_id, overrides)
