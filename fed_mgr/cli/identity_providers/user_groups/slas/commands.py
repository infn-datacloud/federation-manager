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
from fed_mgr.v1 import IDPS_PREFIX, SLAS_PREFIX, USER_GROUPS_PREFIX

app = typer.Typer()


@app.command()
def create(
    idp_id: Annotated[str, typer.Argument(help="Parent identity provider ID")],
    user_group_id: Annotated[str, typer.Argument(help="Parent user group ID")],
    data: Annotated[str, typer.Argument(help="SLA creation data")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Create a SLA with the given attributes in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{IDPS_PREFIX}/{idp_id}/{USER_GROUPS_PREFIX}"
    url += f"/{user_group_id}/{SLAS_PREFIX}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(url, headers=headers, data=data)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_create_result(resp)


@app.command(name="list")
def get_list(
    idp_id: Annotated[str, typer.Argument(help="Parent identity provider ID")],
    user_group_id: Annotated[str, typer.Argument(help="Parent user group ID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve list of SLAs registered in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{IDPS_PREFIX}/{idp_id}/{USER_GROUPS_PREFIX}"
    url += f"/{user_group_id}/{SLAS_PREFIX}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def get(
    idp_id: Annotated[str, typer.Argument(help="Parent identity provider ID")],
    user_group_id: Annotated[str, typer.Argument(help="Parent user group ID")],
    id: Annotated[str, typer.Argument(help="SLA UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Retrieve SLA registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{IDPS_PREFIX}/{idp_id}/{USER_GROUPS_PREFIX}"
    url += f"/{user_group_id}/{SLAS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_get_result(resp)


@app.command()
def patch(
    idp_id: Annotated[str, typer.Argument(help="Parent identity provider ID")],
    user_group_id: Annotated[str, typer.Argument(help="Parent user group ID")],
    id: Annotated[str, typer.Argument(help="SLA UUID")],
    data: Annotated[str, typer.Argument(help="SLA patch data")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Patch the SLA registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{IDPS_PREFIX}/{idp_id}/{USER_GROUPS_PREFIX}"
    url += f"/{user_group_id}/{SLAS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.patch(url, headers=headers, data=data)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_patch_result(resp)


@app.command()
def delete(
    idp_id: Annotated[str, typer.Argument(help="Parent identity provider ID")],
    user_group_id: Annotated[str, typer.Argument(help="Parent user group ID")],
    id: Annotated[str, typer.Argument(help="SLA UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Delete the SLA registered in the Fed-Mgr and matching the given ID.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{IDPS_PREFIX}/{idp_id}/{USER_GROUPS_PREFIX}"
    url += f"/{user_group_id}/{SLAS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_delete_result(resp)
