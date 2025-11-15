"""Module with utils and config for the CLI."""

from typing import Annotated

import requests
import typer


def default_base_url() -> str:
    """Return the default base url for fed-mgr."""
    return "http://localhost:8000/api/v1"


FedMgrUrlDep = Annotated[
    str,
    typer.Option(
        default_factory=default_base_url,
        envvar="FED_MGR_URL",
        help="Federation-Manager base URL",
    ),
]
TokenDep = Annotated[
    str,
    typer.Option(envvar="FED_MGR_TOKEN", help="User token to attach to the request"),
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
        case 409:
            data = resp.json()
            print(f"Conflict: {data['detail']}")
        case 422:
            data = resp.json()
            print(f"Unprocessable content: {data['detail']}")
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
        case 409:
            data = resp.json()
            print(f"Conflict: {data['detail']}")
        case 422:
            data = resp.json()
            print(f"Unprocessable content: {data['detail']}")
        case _:
            print(f"Unexpected status-code: {resp.status_code}")
