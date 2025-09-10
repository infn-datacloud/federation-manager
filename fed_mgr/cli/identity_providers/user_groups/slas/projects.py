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
)
from fed_mgr.v1 import IDPS_PREFIX, PROJECTS_PREFIX, SLAS_PREFIX, USER_GROUPS_PREFIX

app = typer.Typer()


@app.command()
def connect(
    idp_id: Annotated[str, typer.Argument(help="Parent identity provider ID")],
    user_group_id: Annotated[str, typer.Argument(help="Parent user group ID")],
    sla_id: Annotated[str, typer.Argument(help="Parent SLA ID")],
    data: Annotated[str, typer.Argument(help="SLA creation data")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Connect a project to an SLA in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{IDPS_PREFIX}/{idp_id}/{USER_GROUPS_PREFIX}"
    url += f"/{user_group_id}/{SLAS_PREFIX}/{sla_id}/{PROJECTS_PREFIX}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.post(url, headers=headers, data=data)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_create_result(resp)


@app.command()
def disconnect(
    idp_id: Annotated[str, typer.Argument(help="Parent identity provider ID")],
    user_group_id: Annotated[str, typer.Argument(help="Parent user group ID")],
    sla_id: Annotated[str, typer.Argument(help="Parent SLA ID")],
    id: Annotated[str, typer.Argument(help="SLA UUID")],
    base_url: FedMgrUrlDep,
    token: TokenDep,
):
    """Disconnect a project, matching the given ID, from an SLA in the Fed-Mgr.

    If --token is used, it overrides the default written in env var FED_MGR_TOKEN.
    If --base_url is used, it overrides the default written in env var FED_MGR_URL.
    """
    url = f"{base_url}{IDPS_PREFIX}/{idp_id}/{USER_GROUPS_PREFIX}"
    url += f"/{user_group_id}/{SLAS_PREFIX}/{sla_id}/{PROJECTS_PREFIX}/{id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.delete(url, headers=headers)
    except ConnectionError:
        print(f"Can't connect to URL {url}")
        return

    evaluate_delete_result(resp)


if __name__ == "__main__":
    app()
