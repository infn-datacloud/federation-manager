"""Unit tests for provider dependencies in fed_mgr.v1.providers.dependencies.

Covers:
- provider_required: ensures 404 is raised if provider is None, otherwise does
    nothing.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from fed_mgr.exceptions import ItemNotFoundError
from fed_mgr.v1.providers.dependencies import provider_required


def test_provider_required_success():
    """Test provider_required does nothing if provider is present."""
    provider_id = uuid.uuid4()
    provider = MagicMock()  # Simulate found resource provider
    # Should not raise
    assert provider_required(provider_id, provider) == provider


def test_provider_required_not_found():
    """Test provider_required raises 404 if provider is None."""
    provider_id = uuid.uuid4()
    provider = None
    with pytest.raises(
        ItemNotFoundError,
        match=f"Provider with ID '{provider_id!s}' does not exist",
    ):
        provider_required(provider_id, provider)
