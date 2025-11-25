"""Fixtures for fed-mgr tests."""

import logging
import os
from typing import Callable
from unittest import mock

import pytest
from cryptography.fernet import Fernet

import fed_mgr.config as conf
from fed_mgr.config import Settings

# Store original get_settings for any needs and override the module's get_settings
original_get_settings_func = conf.get_settings
os.environ.clear()
conf.get_settings = lambda: Settings(
    SECRET_KEY=Fernet.generate_key(), _env_file=".test.env"
)


@pytest.fixture
def logger():
    """Fixture that returns a mock logger object for testing purposes."""
    return mock.MagicMock(spec=logging.Logger)


@pytest.fixture
def overwrite_env_file_field() -> dict[str, str]:
    """Use a not existing .env file."""
    return {"_env_file": ".test.env"}


@pytest.fixture
def mandatory_settings_fields(
    overwrite_env_file_field: dict[str, str],
) -> dict[str, str | bytes]:
    """Set a valid SECRET_KEY."""
    return {**overwrite_env_file_field, "SECRET_KEY": Fernet.generate_key()}


@pytest.fixture
def original_get_settings() -> Callable:
    """Return the not patched get_settings function."""
    return original_get_settings_func
