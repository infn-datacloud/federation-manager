"""Unit tests for project dependencies in fed_mgr.v1.providers.projects.dependencies.

Covers:
- project_required: ensures 404 is raised if parent_project is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from fed_mgr.v1.providers.projects.dependencies import project_required


def test_project_required_success():
    """Test project_required does nothing if parent_project is present."""
    request = MagicMock()
    project_id = uuid.uuid4()
    parent_project = MagicMock()  # Simulate found resource project

    # Should not raise
    assert project_required(request, project_id, parent_project) == parent_project


def test_project_required_not_found(mock_logger):
    """Test project_required raises 404 if parent_project is None."""
    request = MagicMock()
    project_id = uuid.uuid4()
    parent_project = None
    request.state.logger = mock_logger

    with pytest.raises(HTTPException) as exc:
        project_required(request, project_id, parent_project)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert f"Project with ID '{project_id!s}' does not exist" in str(exc.value.detail)
    request.state.logger.error.assert_called_once()
