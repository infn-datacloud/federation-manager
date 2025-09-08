"""Module with the CLI commands."""

from typing import Annotated

import requests
import typer
from requests.exceptions import ConnectionError

from fed_mgr.cli.utils import (
    TokenDep,
    evaluate_create_result,
    evaluate_delete_result,
    evaluate_get_result,
    get_settings,
    retrieve_token,
)
from fed_mgr.v1 import USERS_PREFIX

app = typer.Typer()


@app.command()
def create_me(token: TokenDep = None):
    """Retrieve user registered in the Federation-Manager and matching the given ID.

    If --token is used, it overrides the default written in env var USER_TOKEN.
    """
    settings = get_settings()
    url = f"{settings.FED_MGR_URL}{USERS_PREFIX}"
    token = retrieve_token(token, settings)
    if token is None:
        return

    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_create_result(resp)


@app.command(name="list")
def get_list(token: TokenDep = None):
    """Retrieve list of users registered in the Federation-Manager.

    If --token is used, it overrides the default written in env var USER_TOKEN.
    """
    settings = get_settings()
    url = f"{settings.FED_MGR_URL}{USERS_PREFIX}"
    token = retrieve_token(token, settings)
    if token is None:
        return

    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def get(id: Annotated[str, typer.Argument(help="User UUID")], token: TokenDep = None):
    """Retrieve user registered in the Federation-Manager and matching the given ID.

    If --token is used, it overrides the default written in env var USER_TOKEN.
    """
    settings = get_settings()
    url = f"{settings.FED_MGR_URL}{USERS_PREFIX}/{id}"
    token = retrieve_token(token, settings)
    if token is None:
        return

    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def delete(
    id: Annotated[str, typer.Argument(help="User UUID")], token: TokenDep = None
):
    """Retrieve user registered in the Federation-Manager and matching the given ID.

    If --token is used, it overrides the default written in env var USER_TOKEN.
    """
    settings = get_settings()
    url = f"{settings.FED_MGR_URL}{USERS_PREFIX}/{id}"
    token = retrieve_token(token, settings)
    if token is None:
        return

    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_delete_result(resp)


if __name__ == "__main__":
    app()
