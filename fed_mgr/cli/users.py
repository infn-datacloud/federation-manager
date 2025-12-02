"""Module with the CLI commands."""

from typing import Annotated

import requests
import typer
from requests.exceptions import ConnectionError

from fed_mgr.cli.utils import (
    FedMgrUrlDep,
    TokenDep,
    evaluate_create_result,
    evaluate_delete_result,
    evaluate_get_result,
)
from fed_mgr.v1 import USERS_PREFIX

app = typer.Typer()


@app.command()
def create_me(base_url: FedMgrUrlDep, token: TokenDep):
    """Create user matching token details in the Federation-Manager.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{USERS_PREFIX}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_create_result(resp)


@app.command(name="list")
def get_list(base_url: FedMgrUrlDep, token: TokenDep):
    """Retrieve list of users registered in the Federation-Manager.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{USERS_PREFIX}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def get(
    id: Annotated[str, typer.Argument(help="User UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve user registered in the Federation-Manager and matching the given ID.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{USERS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def delete(
    id: Annotated[str, typer.Argument(help="User UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Delete the user registered in the Federation-Manager and matching the given ID.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{USERS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_delete_result(resp)


if __name__ == "__main__":
    app()
