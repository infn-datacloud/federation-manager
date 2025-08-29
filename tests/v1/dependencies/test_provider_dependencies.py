"""Unit tests for provider dependencies in fed_mgr.v1.providers.dependencies.

Covers:
- provider_required: ensures 404 is raised if parent_provider is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from fed_mgr.v1.providers.dependencies import provider_required


def test_provider_required_success():
    """Test provider_required does nothing if parent_provider is present."""
    request = MagicMock()
    provider_id = uuid.uuid4()
    parent_provider = MagicMock()  # Simulate found resource provider

    # Should not raise
    assert provider_required(request, provider_id, parent_provider) == parent_provider


def test_provider_required_not_found(mock_logger):
    """Test provider_required raises 404 if parent_provider is None."""
    request = MagicMock()
    provider_id = uuid.uuid4()
    parent_provider = None
    request.state.logger = mock_logger

    with pytest.raises(HTTPException) as exc:
        provider_required(request, provider_id, parent_provider)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert f"Resource provider with ID '{provider_id!s}' does not exist" in str(
        exc.value.detail
    )
    request.state.logger.error.assert_called_once()
