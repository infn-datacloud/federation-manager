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
from fed_mgr.v1 import PROJECTS_PREFIX, PROVIDERS_PREFIX

app = typer.Typer()


@app.command()
def create(
    provider_id: Annotated[str, typer.Argument(help="Parent provider ID")],
    data: Annotated[str, typer.Argument(help="Project creation data")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Create a project with the given attributes in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(url, headers=headers, data=data)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_create_result(resp)


@app.command(name="list")
def get_list(
    provider_id: Annotated[str, typer.Argument(help="Parent provider ID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve list of projects registered in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def get(
    provider_id: Annotated[str, typer.Argument(help="Parent provider ID")],
    id: Annotated[str, typer.Argument(help="Project UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve project registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def patch(
    provider_id: Annotated[str, typer.Argument(help="Parent provider ID")],
    id: Annotated[str, typer.Argument(help="Project UUID")],
    data: Annotated[str, typer.Argument(help="Project patch data")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Patch the project registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.patch(url, headers=headers, data=data)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_patch_result(resp)


@app.command()
def delete(
    provider_id: Annotated[str, typer.Argument(help="Parent provider ID")],
    id: Annotated[str, typer.Argument(help="Project UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Delete the project registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_delete_result(resp)
