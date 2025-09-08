"""Module with utils and config for the CLI."""

from functools import lru_cache
from typing import Annotated

import requests
import typer
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CliSettings(BaseSettings):
    """Settings for CLI."""

    FED_MGR_URL: Annotated[
        AnyHttpUrl,
        Field(
            default="http://localhost:8000/api/v1",
            description="Federation-Manager base URL",
        ),
    ]
    FED_MGR_TOKEN: Annotated[str | None, Field(default=None, description="User token")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> CliSettings:
    """Retrieve cached settings."""
    return CliSettings()


def retrieve_token(cli_token: str, settings: CliSettings) -> str | None:
    """Return the token from env var or from cli.

    In any case verify token signature.
    """
    if cli_token is not None:
        return cli_token
    if settings.FED_MGR_TOKEN is not None:
        return settings.FED_MGR_TOKEN
    print(
        "No token provided. Either edit the env variable FED_MGR_TOKEN or pass it using"
        " the '--token' argument."
    )


TokenDep = Annotated[
    str | None, typer.Option(help="User token to attach to the request")
]


def evaluate_create_result(resp: requests.Response) -> None:
    """Log message based on resp status code."""
    match resp.status_code:
        case 201:
            data = resp.json()
            print(data)
        case 401:
            data = resp.json()
            print(f"Unauthorized: {data['detail']}")
        case 403:
            data = resp.json()
            print(f"Forbidden: {data['detail']}")
        case _:
            print(f"Unexpected status-code: {resp.status_code}")


def evaluate_get_result(resp: requests.Response) -> None:
    """Log message based on resp status code."""
    match resp.status_code:
        case 200:
            data = resp.json()
            print(data)
        case 401:
            data = resp.json()
            print(f"Unauthorized: {data['detail']}")
        case 403:
            data = resp.json()
            print(f"Forbidden: {data['detail']}")
        case _:
            print(f"Unexpected status-code: {resp.status_code}")


def evaluate_delete_result(resp: requests.Response) -> None:
    """Log message based on resp status code."""
    match resp.status_code:
        case 204:
            print("Deleted")
        case 401:
            data = resp.json()
            print(f"Unauthorized: {data['detail']}")
        case 403:
            data = resp.json()
            print(f"Forbidden: {data['detail']}")
        case _:
            print(f"Unexpected status-code: {resp.status_code}")


def evaluate_patch_result(resp: requests.Response) -> None:
    """Log message based on resp status code."""
    match resp.status_code:
        case 204:
            print("Patched")
        case 401:
            data = resp.json()
            print(f"Unauthorized: {data['detail']}")
        case 403:
            data = resp.json()
            print(f"Forbidden: {data['detail']}")
        case _:
            print(f"Unexpected status-code: {resp.status_code}")
