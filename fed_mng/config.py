"""Module with the configuration parameters."""
import os
from functools import lru_cache
from typing import Any

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, validator


class Settings(BaseSettings):
    """Model with the app settings."""

    PROJECT_NAME: str = "Federation-Manager"
    DOMAIN: str = "localhost:8000"
    API_V1_STR: str = "/api/v1"

    @validator("API_V1_STR")
    @classmethod
    def start_with_single_slash(cls, v: str) -> str:
        """String must start with a single slash."""
        assert v.startswith("/"), ValueError("API V1 string must start with '/'")
        assert len(v) > 1, ValueError(
            "API V1 string can't have an empty string after the '/'"
        )
        return v

    MAINTAINER_NAME: str | None = None
    MAINTAINER_URL: AnyHttpUrl | None = None
    MAINTAINER_EMAIL: EmailStr | None = None

    TRUSTED_IDP_LIST: list[AnyHttpUrl] = []

    DOC_V1_URL: AnyHttpUrl | None = None

    @validator("DOC_V1_URL", pre=True)
    @classmethod
    def create_doc_url(cls, v: str | None, values: dict[str, Any]) -> str:
        """Build URL for internal documentation."""
        if v:
            return v
        protocol = "http"
        link = os.path.join(values.get("DOMAIN"), values.get("API_V1_STR")[1:], "docs")
        return f"{protocol}://{link}"

    class Config:
        """Sub class to set attribute as case sensitive."""

        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Retrieve cached settings."""
    return Settings()
