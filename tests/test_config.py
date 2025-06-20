"""Unit tests for fed_mgr.config module.

These tests cover:
- LogLevelEnum and AuthorizationMethodsEnum values
- get_level function for various input types
- Settings model field defaults and types
- get_settings caching
"""

import logging

from pydantic import AnyHttpUrl

from fed_mgr.config import (
    AuthenticationMethodsEnum,
    AuthorizationMethodsEnum,
    LogLevelEnum,
    Settings,
    get_level,
    get_settings,
)


def test_authentication_methods_enum_values():
    """Test that AuthenticationMethodsEnum values are correct."""
    assert AuthenticationMethodsEnum.local == "local"


def test_authorization_methods_enum_values():
    """Test that AuthorizationMethodsEnum values are correct."""
    assert AuthorizationMethodsEnum.opa == "opa"


def test_log_level_enum_values():
    """Test that LogLevelEnum values match the standard logging levels."""
    assert LogLevelEnum.DEBUG == logging.DEBUG
    assert LogLevelEnum.INFO == logging.INFO
    assert LogLevelEnum.WARNING == logging.WARNING
    assert LogLevelEnum.ERROR == logging.ERROR
    assert LogLevelEnum.CRITICAL == logging.CRITICAL


def test_get_level_with_string():
    """Test get_level with string input returns the correct logging level."""
    assert get_level("info") == logging.INFO
    assert get_level("DEBUG") == logging.DEBUG
    assert get_level("warning") == logging.WARNING


def test_get_level_with_enum():
    """Test get_level with LogLevelEnum input returns the correct logging level."""
    assert get_level(LogLevelEnum.ERROR) == logging.ERROR


def test_get_level_with_int():
    """Test get_level with integer input returns the same integer."""
    assert get_level(logging.CRITICAL) == logging.CRITICAL


def test_settings_defaults():
    """Test that Settings model has correct default values and types."""
    s = Settings()
    assert s.PROJECT_NAME == "Federation-Manager"
    assert s.BASE_URL == AnyHttpUrl("http://localhost:8000")
    assert isinstance(s.LOG_LEVEL, LogLevelEnum)
    assert isinstance(s.AUTHN_MODE, (str, type(None)))
    assert isinstance(s.AUTHZ_MODE, (str, type(None)))
    assert isinstance(s.MAINTAINER_NAME, (str, type(None)))
    assert isinstance(s.MAINTAINER_URL, (str, type(None))) or s.MAINTAINER_URL is None
    assert (
        isinstance(s.MAINTAINER_EMAIL, (str, type(None))) or s.MAINTAINER_EMAIL is None
    )
    assert isinstance(s.DB_URL, str)
    assert isinstance(s.OPA_AUTHZ_URL, str) or s.OPA_AUTHZ_URL is not None
    assert isinstance(s.DB_ECO, bool)
    assert isinstance(s.TRUSTED_IDP_LIST, list)
    assert isinstance(s.BACKEND_CORS_ORIGINS, list)


def test_get_settings_caching():
    """Test that get_settings returns a cached Settings instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
