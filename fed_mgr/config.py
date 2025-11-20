"""Module with the configuration parameters."""

import logging
from enum import Enum
from functools import lru_cache
from typing import Annotated, Literal

from cryptography.fernet import Fernet
from fastapi import Depends
from pydantic import (
    AfterValidator,
    AnyHttpUrl,
    BeforeValidator,
    EmailStr,
    Field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

API_V1_STR = "/api/v1/"


class AuthenticationMethodsEnum(str, Enum):
    """Enumeration of supported authentication methods."""

    local = "local"


class AuthorizationMethodsEnum(str, Enum):
    """Enumeration of supported authorization methods."""

    opa = "opa"


class LogLevelEnum(int, Enum):
    """Enumeration of supported logging levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def get_level(value: int | str | LogLevelEnum) -> int:
    """Convert a string, integer, or LogLevelEnum value to a logging level integer.

    Args:
        value: The log level as a string (case-insensitive), integer, or LogLevelEnum.

    Returns:
        int: The corresponding logging level integer.

    """
    if isinstance(value, str) and value.upper() in LogLevelEnum.__members__:
        return LogLevelEnum.__getitem__(value.upper())
    return value


class Settings(BaseSettings):
    """Model with the app settings."""

    PROJECT_NAME: Annotated[
        str,
        Field(
            default="Federation-Manager",
            description="Project name to show in the Swagger documentation",
        ),
    ]
    MAINTAINER_NAME: Annotated[
        str | None, Field(default=None, description="Maintainer name")
    ]
    MAINTAINER_URL: Annotated[
        AnyHttpUrl | None, Field(default=None, description="Maintainer's profile URL")
    ]
    MAINTAINER_EMAIL: Annotated[
        EmailStr | None, Field(default=None, description="Maintainer's email address")
    ]
    LOG_LEVEL: Annotated[
        LogLevelEnum,
        Field(default=LogLevelEnum.INFO, description="Logs level"),
        BeforeValidator(get_level),
    ]
    BASE_URL: Annotated[
        AnyHttpUrl,
        Field(
            default="http://localhost:8000",
            description="Application base URL. "
            "Used to build documentation redirect links.",
        ),
    ]
    DB_URL: Annotated[
        str,
        Field(
            default="sqlite+pysqlite:///:memory:",
            description="DB URL. By default it use an in memory SQLite DB.",
        ),
    ]
    DB_SCHEME: Annotated[
        str | None,
        Field(
            default=None, description="Database type and library (i.e mysql+pymysql)"
        ),
    ]
    DB_USER: Annotated[str | None, Field(default=None, description="Database user")]
    DB_PASSWORD: Annotated[
        str | None, Field(default=None, description="Database user password")
    ]
    DB_HOST: Annotated[str | None, Field(default=None, description="Database hostname")]
    DB_PORT: Annotated[
        int | None, Field(default=None, ge=1, description="Database exposed port")
    ]
    DB_NAME: Annotated[
        str | None,
        Field(default=None, description="Name of the database's schema to use"),
    ]
    DB_ECO: Annotated[
        bool, Field(default=False, description="Eco messages exchanged with the DB")
    ]
    AUTHN_MODE: Annotated[
        AuthenticationMethodsEnum | None,
        Field(
            default=None,
            description="Authorization method to use. Allowed values: local",
        ),
    ]
    AUTHZ_MODE: Annotated[
        AuthorizationMethodsEnum | None,
        Field(
            default=None,
            description="Authorization method to use. Allowed values: opa",
        ),
    ]
    TRUSTED_IDP_LIST: Annotated[
        list[AnyHttpUrl],
        Field(
            default_factory=list,
            description="List of the application trusted identity providers",
        ),
    ]
    IDP_TIMEOUT: Annotated[
        int, Field(default=5, ge=0, description="Communication timeout (s) for IDP")
    ]
    OPA_AUTHZ_URL: Annotated[
        AnyHttpUrl,
        Field(
            default="http://localhost:8181/v1/data/fed_mgr",
            description="Open Policy Agent service roles authorization URL",
        ),
    ]
    OPA_TIMEOUT: Annotated[
        int, Field(default=5, ge=0, description="Communication timeout (s) for OPA")
    ]
    API_KEY: Annotated[
        str | None,
        Field(
            default=None,
            description="API Key to set into the header field 'X-API-Key'",
        ),
    ]
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyHttpUrl | Literal["*"]],
        Field(
            default=["http://localhost:3000/"],
            description="JSON-formatted list of allowed origins",
        ),
    ]
    KAFKA_ENABLED: Annotated[bool, Field(
      default=True,
      description="Enable Kafka consumer"
    )]
    KAFKA_BOOTSTRAP_SERVERS: Annotated[str, Field(
        default="host.docker.internal:9092",
        description="Kafka address or comma separated list of addresses"
    )]
    KAFKA_EVALUATE_PROVIDERS_TOPIC: Annotated[
        str,
        Field(
            default="evaluate-providers",
            description="Kafka topic with for providers to evaluated before federation request approval.",
        )
    ]
    KAFKA_FEDERATION_TESTS_RESULT_TOPIC: Annotated[
        str,
        Field(
            default="federation-tests-result",
            description="Kafka topic for rally tests results",
        )
    ]
    KAFKA_PROVIDERS_MONITORING_TOPIC: Annotated[
        str,
        Field(
            default="providers-monitoring",
            description="Kafka topic for periodic tests results of the federated providers.",
        )
    ]
    KAFKA_TIMEOUT: Annotated[
        int,
        Field(
            default=10000,
            ge=0,
            description="Message timeout in milliseconds.",
        )
    ]
    KAFKA_MAX_REQUEST_SIZE: Annotated[
        int,
        Field(
            default=104857600,
            ge=0,
            description="Maximum size of the request to send in bytes.",
        ),
    ]
    KAFKA_CLIENT_NAME: Annotated[
        str,
        Field(
            default="fedmgr", description="Kafka client name."
        )
    ]
    KAFKA_SSL_CACERT_PATH: Annotated[
        str | None, Field(default=None, description="Path to the SSL CA cert file.")
    ]
    KAFKA_SSL_CERT_PATH: Annotated[
        str | None, Field(default=None, description="Path to the SSL cert file.")
    ]
    KAFKA_SSL_KEY_PATH: Annotated[
        str | None, Field(default=None, description="Path to the SSL Key file.")
    ]
    KAFKA_SSL_PASSWORD: Annotated[
        str | None, Field(default=None, description="Private key decryption password.")
    ]
    SECRET_KEY: Annotated[
        bytes | Fernet,
        Field(
            description="Secret key used to encrypt values. To generate a valid key "
            "run the following command in shell and copy the generated output: "
            '`python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"`'
        ),
        AfterValidator(lambda x: Fernet(x) if isinstance(x, bytes) else x),
    ]

    model_config = SettingsConfigDict(env_file=".env")

    @model_validator(mode="after")
    def verify_authn_authz_mode(self) -> Self:
        """Validate the configuration of authentication and authorization modes.

        Raises:
            ValueError: If the authorization mode is defined but the authentication mode
            is undefined.

        Returns:
            Self: Returns the current instance for method chaining.

        """
        if self.AUTHN_MODE is None and self.AUTHZ_MODE is not None:
            raise ValueError(
                "If authorization mode is defined, authentication mode can't be "
                "undefined."
            )
        return self

    @model_validator(mode="after")
    def build_db_url(self) -> Self:
        """Replace DB_URL with one build from the single values.

        If any of the involved value is None, keep the existing one. If port is None,
        the default one, for that DB type, is used.

        Returns:
            Self: Returns the current instance for method chaining.

        """
        if (
            self.DB_SCHEME is not None
            and self.DB_USER is not None
            and self.DB_PASSWORD is not None
            and self.DB_HOST is not None
            and self.DB_NAME is not None
        ):
            if self.DB_PORT is None:
                self.DB_URL = f"{self.DB_SCHEME}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"
            else:
                self.DB_URL = f"{self.DB_SCHEME}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return self


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached settings."""
    return Settings() # type: ignore


SettingsDep = Annotated[Settings, Depends(get_settings)]
