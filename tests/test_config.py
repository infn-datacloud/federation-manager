"""Unit tests for fed_mgr.config module.

These tests cover:
- LogLevelEnum and AuthorizationMethodsEnum values
- get_level function for various input types
- Settings model field defaults and types
- get_settings caching
"""

import logging

import pytest
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
    s = Settings(_env_file=".test.env")
    assert s.PROJECT_NAME == "Federation-Manager"
    assert isinstance(s.MAINTAINER_NAME, (str, type(None)))
    assert isinstance(s.MAINTAINER_URL, (str, type(None)))
    assert isinstance(s.MAINTAINER_EMAIL, (str, type(None)))
    assert isinstance(s.LOG_LEVEL, LogLevelEnum)
    assert s.BASE_URL == AnyHttpUrl("http://localhost:8000")
    assert s.DB_URL == "sqlite+pysqlite:///:memory:"
    assert s.DB_ECO is False
    assert isinstance(s.AUTHN_MODE, (AuthenticationMethodsEnum, type(None)))
    assert isinstance(s.AUTHZ_MODE, (AuthorizationMethodsEnum, type(None)))
    assert isinstance(s.TRUSTED_IDP_LIST, list)
    assert s.OPA_AUTHZ_URL == AnyHttpUrl("http://localhost:8181/v1/data/fed_mgr")
    assert isinstance(s.BACKEND_CORS_ORIGINS, list)
    assert s.KAFKA_ENABLE is False
    assert isinstance(s.KAFKA_BOOTSTRAP_SERVERS, str)
    assert isinstance(s.KAFKA_EVALUATE_PROVIDERS_TOPIC, str)
    assert isinstance(s.KAFKA_FEDERATION_TESTS_RESULT_TOPIC, str)
    assert isinstance(s.KAFKA_PROVIDERS_MONITORING_TOPIC, str)
    assert isinstance(s.KAFKA_TOPIC_TIMEOUT, int)
    assert isinstance(s.KAFKA_MAX_REQUEST_SIZE, int)
    assert isinstance(s.KAFKA_CLIENT_NAME, str)
    assert s.KAFKA_SSL_ENABLE is False
    assert isinstance(s.KAFKA_SSL_CACERT_PATH, (str, type(None)))
    assert isinstance(s.KAFKA_SSL_CERT_PATH, (str, type(None)))
    assert isinstance(s.KAFKA_SSL_KEY_PATH, (str, type(None)))
    assert isinstance(s.KAFKA_SSL_PASSWORD, (str, type(None)))
    assert s.KAFKA_ALLOW_AUTO_CREATE_TOPICS is False
    assert isinstance(s.KAFKA_EVALUATE_PROVIDERS_MSG_VERSION, str)
    assert isinstance(s.KAFKA_FEDERATION_TESTS_RESULT_MSG_VERSION, str)
    assert isinstance(s.KAFKA_PROVIDERS_MONITORING_MSG_VERSION, str)


def test_get_settings_caching():
    """Test that get_settings returns a cached Settings instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_settings_authz_without_authn_raises():
    """Test that ValueError is raised if AUTHZ_MODE is set but AUTHN_MODE is None."""
    with pytest.raises(ValueError) as exc:
        Settings(AUTHN_MODE=None, AUTHZ_MODE=AuthorizationMethodsEnum.opa)
    assert "authorization mode is defined" in str(exc.value)
