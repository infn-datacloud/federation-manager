"""Unit tests for project dependencies in fed_mgr.v1.providers.projects.dependencies.

Covers:
- project_required: ensures 404 is raised if parent_project is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.providers.identity_providers.dependencies import idp_overrides_required


def test_idp_overrides_required_success():
    """Test project_required does nothing if parent_project is present."""
    provider_id = uuid.uuid4()
    idp_id = uuid.uuid4()
    overrides = MagicMock()  # Simulate found resource project
    # Should not raise
    assert idp_overrides_required(provider_id, idp_id, overrides) == overrides


def test_idp_overrides_required_not_found():
    """Test project_required raises 404 if parent_project is None."""
    provider_id = uuid.uuid4()
    idp_id = uuid.uuid4()
    overrides = None

    message = f"Provider with ID '{provider_id!s}' does not define overrides for "
    message += f"identity provider with ID '{idp_id!s}'"
    with pytest.raises(ItemNotFoundError, match=message):
        idp_overrides_required(provider_id, idp_id, overrides)
