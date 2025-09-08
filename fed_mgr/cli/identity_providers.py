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
    evaluate_patch_result,
)
from fed_mgr.v1 import IDPS_PREFIX

app = typer.Typer()


@app.command()
def create(
    idp: Annotated[str, typer.Argument(help="Identity provider creation data")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve identity provider registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var USER_TOKEN.
    """
    url = f"{base_url}{IDPS_PREFIX}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(url, headers=headers, data=idp)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_create_result(resp)


@app.command(name="list")
def get_list(base_url: FedMgrUrlDep, token: TokenDep):
    """Retrieve list of identity providers registered in the Fed-Mgr.

    If --token is used, it overrides the default written in env var USER_TOKEN.
    """
    url = f"{base_url}{IDPS_PREFIX}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def get(
    id: Annotated[str, typer.Argument(help="Identity provider UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve identity provider registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var USER_TOKEN.
    """
    url = f"{base_url}{IDPS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def patch(
    id: Annotated[str, typer.Argument(help="Identity provider UUID")],
    idp: Annotated[str, typer.Argument(help="Identity provider patch data")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve identity provider registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var USER_TOKEN.
    """
    url = f"{base_url}{IDPS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.patch(url, headers=headers, data=idp)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_patch_result(resp)


@app.command()
def delete(
    id: Annotated[str, typer.Argument(help="Identity provider UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve identity provider registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var USER_TOKEN.
    """
    url = f"{base_url}{IDPS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_delete_result(resp)


if __name__ == "__main__":
    app()
