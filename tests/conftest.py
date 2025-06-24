"""Fixtures for fed-mgr tests."""

from unittest import mock

import pytest


@pytest.fixture
def mock_logger():
    """Fixture that returns a mock logger object for testing purposes."""
    logger = mock.Mock()
    return logger
