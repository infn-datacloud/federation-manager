"""Fixtures for fed-mgr tests."""

from unittest import mock

import pytest
from sqlmodel import Session


@pytest.fixture
def session() -> mock.MagicMock:
    """Create and return a mock session object for testing purposes.

    Returns:
        unittest.mock.Mock: A mock session object.

    """
    return mock.MagicMock(spec=Session)
