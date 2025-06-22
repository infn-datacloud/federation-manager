"""Module with the configuration parameters."""

import logging
from enum import Enum
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends
from pydantic import AnyHttpUrl, BeforeValidator, EmailStr, Field, model_validator
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
    if isinstance(value, str):
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
    OPA_AUTHZ_URL: Annotated[
        AnyHttpUrl,
        Field(
            default="http://localhost:8181/v1/data/fed_mgr",
            description="Open Policy Agent service roles authorization URL",
        ),
    ]
    DB_ECO: Annotated[
        bool, Field(default=False, description="Eco messages exchanged with the DB")
    ]
    LOG_LEVEL: Annotated[
        LogLevelEnum,
        Field(default=LogLevelEnum.INFO, description="Logs level"),
        BeforeValidator(get_level),
    ]
    TRUSTED_IDP_LIST: Annotated[
        list[AnyHttpUrl],
        Field(
            default_factory=list,
            description="List of the application trusted identity providers",
        ),
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
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyHttpUrl | Literal["*"]],
        Field(
            default=["http://localhost:3000/"],
            description="JSON-formatted list of allowed origins",
        ),
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


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached settings."""
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
