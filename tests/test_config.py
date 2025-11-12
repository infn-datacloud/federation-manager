"""Unit tests for fed_mgr.config module.

These tests cover:
- LogLevelEnum and AuthorizationMethodsEnum values
- get_level function for various input types
- Settings model field defaults and types
- get_settings caching
"""

import logging
import os

import pytest
from cryptography.fernet import Fernet
from pydantic import AnyHttpUrl

from fed_mgr.config import (
    AuthenticationMethodsEnum,
    AuthorizationMethodsEnum,
    Settings,
    get_level,
)
from fed_mgr.logger import LogLevelEnum


def test_authentication_methods_enum_values() -> None:
    """Test that AuthenticationMethodsEnum values are correct."""
    assert AuthenticationMethodsEnum.local == "local"


def test_authorization_methods_enum_values() -> None:
    """Test that AuthorizationMethodsEnum values are correct."""
    assert AuthorizationMethodsEnum.opa == "opa"


def test_get_level_with_string() -> None:
    """Test get_level with string input returns the correct logging level."""
    assert get_level("info") == logging.INFO
    assert get_level("debug") == logging.DEBUG
    assert get_level("warning") == logging.WARNING
    assert get_level("error") == logging.ERROR
    assert get_level("critical") == logging.CRITICAL
    assert get_level("INFO") == logging.INFO
    assert get_level("DEBUG") == logging.DEBUG
    assert get_level("WARNING") == logging.WARNING
    assert get_level("ERROR") == logging.ERROR
    assert get_level("CRITICAL") == logging.CRITICAL


def test_get_level_with_enum() -> None:
    """Test get_level with LogLevelEnum input returns the correct logging level."""
    assert get_level(LogLevelEnum.INFO) == logging.INFO
    assert get_level(LogLevelEnum.DEBUG) == logging.DEBUG
    assert get_level(LogLevelEnum.WARNING) == logging.WARNING
    assert get_level(LogLevelEnum.ERROR) == logging.ERROR
    assert get_level(LogLevelEnum.CRITICAL) == logging.CRITICAL


def test_get_level_with_int() -> None:
    """Test get_level with integer input returns the same integer."""
    assert get_level(logging.INFO) == logging.INFO
    assert get_level(logging.DEBUG) == logging.DEBUG
    assert get_level(logging.WARNING) == logging.WARNING
    assert get_level(logging.ERROR) == logging.ERROR
    assert get_level(logging.CRITICAL) == logging.CRITICAL


def test_settings_defaults(mandatory_settings_fields: dict[str, str | bytes]) -> None:
    """Test that Settings model has correct default values and types."""
    s = Settings(**mandatory_settings_fields)
    assert s.PROJECT_NAME == "Federation-Manager"
    assert s.MAINTAINER_NAME is None
    assert s.MAINTAINER_URL is None
    assert s.MAINTAINER_EMAIL is None
    assert s.LOG_LEVEL == LogLevelEnum.INFO
    assert s.BASE_URL == AnyHttpUrl("http://localhost:8000")
    assert s.DB_URL == "sqlite+pysqlite:///:memory:"
    assert s.DB_SCHEME is None
    assert s.DB_USER is None
    assert s.DB_PASSWORD is None
    assert s.DB_HOST is None
    assert s.DB_PORT is None
    assert s.DB_NAME is None
    assert s.DB_ECO is False
    assert s.AUTHN_MODE is None
    assert s.AUTHZ_MODE is None
    assert s.TRUSTED_IDP_LIST == []
    assert s.IDP_TIMEOUT == 5
    assert s.OPA_AUTHZ_URL == AnyHttpUrl("http://localhost:8181/v1/data/fed_mgr")
    assert s.OPA_TIMEOUT == 5
    assert s.API_KEY is None
    assert s.BACKEND_CORS_ORIGINS == [AnyHttpUrl("http://localhost:3000/")]
    assert s.KAFKA_ENABLE is False
    assert s.KAFKA_BOOTSTRAP_SERVERS == "localhost:9092"
    assert s.KAFKA_EVALUATE_PROVIDERS_TOPIC == "evaluate-providers"
    assert s.KAFKA_FEDERATION_TESTS_RESULT_TOPIC == "federation-tests-result"
    assert s.KAFKA_PROVIDERS_MONITORING_TOPIC == "providers-monitoring"
    assert s.KAFKA_TOPIC_TIMEOUT == 1000
    assert s.KAFKA_MAX_REQUEST_SIZE == 104857600
    assert s.KAFKA_CLIENT_NAME == "fedmgr"
    assert s.KAFKA_SSL_ENABLE is False
    assert s.KAFKA_SSL_CACERT_PATH is None
    assert s.KAFKA_SSL_CERT_PATH is None
    assert s.KAFKA_SSL_KEY_PATH is None
    assert s.KAFKA_SSL_PASSWORD is None
    assert s.KAFKA_ALLOW_AUTO_CREATE_TOPICS is False
    assert s.KAFKA_EVALUATE_PROVIDERS_MSG_VERSION == "1.0.0"
    assert s.KAFKA_FEDERATION_TESTS_RESULT_MSG_VERSION == "1.0.0"
    assert s.KAFKA_PROVIDERS_MONITORING_MSG_VERSION == "1.0.0"
    assert s.SECRET_KEY is not None
    assert isinstance(s.SECRET_KEY, Fernet)


def test_get_settings_caching(original_get_settings) -> None:
    """Test that get_settings returns a cached Settings instance."""
    assert (
        callable(original_get_settings)
        and hasattr(original_get_settings, "cache_info")
        and hasattr(original_get_settings, "cache_clear")
    )


def test_settings_invalid_email_raises(
    mandatory_settings_fields: dict[str, str | bytes],
) -> None:
    """Test that Settings model has correct default values and types."""
    with pytest.raises(
        ValueError,
        match="1 validation error for Settings\nMAINTAINER_EMAIL\n  "
        "value is not a valid email address: An email address must have an @-sign",
    ):
        Settings(MAINTAINER_EMAIL="not_an_email", **mandatory_settings_fields)


@pytest.mark.parametrize(
    "key",
    [
        "DB_PORT",
        "IDP_TIMEOUT",
        "OPA_TIMEOUT",
        "KAFKA_TOPIC_TIMEOUT",
        "KAFKA_MAX_REQUEST_SIZE",
    ],
)
def test_settings_negative_value_raises(
    key: str, mandatory_settings_fields: dict[str, str | bytes]
) -> None:
    """Test that Settings model has correct default values and types."""
    with pytest.raises(
        ValueError,
        match=f"1 validation error for Settings\n{key}\n  "
        "Input should be greater than or equal to ",
    ):
        kwargs = {key: -10, **mandatory_settings_fields}
        Settings(**kwargs)


def test_settings_with_invalid_log_level_raises(
    mandatory_settings_fields: dict[str, str | bytes],
) -> None:
    """Test that ValueError is raised if AUTHZ_MODE is set but AUTHN_MODE is None."""
    with pytest.raises(
        ValueError,
        match="1 validation error for Settings\nLOG_LEVEL\n  "
        "Input should be 10, 20, 30, 40 or 50",
    ):
        Settings(LOG_LEVEL="invalid", **mandatory_settings_fields)

    with pytest.raises(
        ValueError,
        match="1 validation error for Settings\nLOG_LEVEL\n  "
        "Input should be 10, 20, 30, 40 or 50",
    ):
        Settings(LOG_LEVEL=99, **mandatory_settings_fields)


def test_settings_with_invalid_secret_key_raises(
    overwrite_env_file_field: dict[str, str],
) -> None:
    """Test that ValueError is raised if AUTHZ_MODE is set but AUTHN_MODE is None."""
    with pytest.raises(
        ValueError,
        match="1 validation error for Settings\nSECRET_KEY\n  Field required",
    ):
        Settings(**overwrite_env_file_field)

    with pytest.raises(
        ValueError,
        match="1 validation error for Settings\nSECRET_KEY\n  Value error, "
        "Fernet key must be 32 url-safe base64-encoded bytes",
    ):
        Settings(SECRET_KEY="changeit", **overwrite_env_file_field)


def test_settings_authz_without_authn_raises(
    mandatory_settings_fields: dict[str, str | bytes],
) -> None:
    """Test that ValueError is raised if AUTHZ_MODE is set but AUTHN_MODE is None."""
    with pytest.raises(
        ValueError,
        match="1 validation error for Settings\n  Value error, "
        "If authorization mode is defined, authentication mode can't be undefined.",
    ):
        Settings(
            AUTHN_MODE=None,
            AUTHZ_MODE=AuthorizationMethodsEnum.opa,
            **mandatory_settings_fields,
        )


def test_build_db_url(mandatory_settings_fields: dict[str, str | bytes]) -> None:
    """Test that ValueError is raised if AUTHZ_MODE is set but AUTHN_MODE is None."""
    scheme = "mysql"
    user = os.getenv("user", "user")
    pwd = os.getenv("password", "password")
    host = "localhost"
    db_name = "db"
    s = Settings(
        DB_SCHEME=scheme,
        DB_USER=user,
        DB_PASSWORD=pwd,
        DB_HOST=host,
        DB_NAME=db_name,
        **mandatory_settings_fields,
    )
    assert s.DB_URL == f"{scheme}://{user}:{pwd}@{host}/{db_name}"

    port = 1234
    s = Settings(
        DB_SCHEME=scheme,
        DB_USER=user,
        DB_PASSWORD=pwd,
        DB_HOST=host,
        DB_PORT=port,
        DB_NAME=db_name,
        **mandatory_settings_fields,
    )
    assert s.DB_URL == f"{scheme}://{user}:{pwd}@{host}:{port}/{db_name}"
