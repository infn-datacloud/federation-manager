"""Fixtures for fed-mgr tests."""

import logging
import os
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def clear_os_environment() -> None:
    """Clear the OS environment."""
    os.environ.clear()


@pytest.fixture
def logger():
    """Fixture that returns a mock logger object for testing purposes."""
    return mock.MagicMock(spec=logging.Logger)
