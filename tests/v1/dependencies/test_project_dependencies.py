"""Unit tests for project dependencies in fed_mgr.v1.providers.projects.dependencies.

Covers:
- project_required: ensures 404 is raised if parent_project is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.providers.projects.dependencies import project_required


def test_project_required_success():
    """Test project_required does nothing if parent_project is present."""
    project_id = uuid.uuid4()
    parent_project = MagicMock()  # Simulate found resource project
    # Should not raise
    assert project_required(project_id, parent_project) == parent_project


def test_project_required_not_found():
    """Test project_required raises 404 if parent_project is None."""
    project_id = uuid.uuid4()
    parent_project = None
    with pytest.raises(
        ItemNotFoundError, match=f"Project with ID '{project_id!s}' does not exist"
    ):
        project_required(project_id, parent_project)
