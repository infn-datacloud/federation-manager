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
from fed_mgr.v1 import PROJECTS_PREFIX, PROVIDERS_PREFIX, REGIONS_PREFIX

app = typer.Typer()


@app.command()
def connect(
    provider_id: Annotated[str, typer.Argument(help="Parent provider ID")],
    project_id: Annotated[str, typer.Argument(help="Parent project ID")],
    data: Annotated[str, typer.Argument(help="Region connection data")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Connect an region to a project with the given attributes in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}"
    url += f"/{project_id}/{REGIONS_PREFIX}"
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
    project_id: Annotated[str, typer.Argument(help="Parent project ID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve list of regions connected to a specific project in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}"
    url += f"/{project_id}/{REGIONS_PREFIX}"
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
    project_id: Annotated[str, typer.Argument(help="Parent project ID")],
    id: Annotated[str, typer.Argument(help="Region UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve the region, matching the given ID, connected to a project in Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}"
    url += f"/{project_id}/{REGIONS_PREFIX}/{id}"
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
    project_id: Annotated[str, typer.Argument(help="Parent project ID")],
    id: Annotated[str, typer.Argument(help="Region UUID")],
    data: Annotated[str, typer.Argument(help="Region patch data")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Patch the override values for an region-project couple in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}"
    url += f"/{project_id}/{REGIONS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.patch(url, headers=headers, data=data)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_patch_result(resp)


@app.command()
def disconnect(
    provider_id: Annotated[str, typer.Argument(help="Parent provider ID")],
    project_id: Annotated[str, typer.Argument(help="Parent project ID")],
    id: Annotated[str, typer.Argument(help="Region UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Disconnect an region from the project in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{PROVIDERS_PREFIX}/{provider_id}/{PROJECTS_PREFIX}"
    url += f"/{project_id}/{REGIONS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_delete_result(resp)
