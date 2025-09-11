"""Module with the user groups subapp."""

import typer

from fed_mgr.cli.identity_providers.user_groups.commands import app as user_groups_app
from fed_mgr.cli.identity_providers.user_groups.slas import app as slas_app

app = typer.Typer()
app.add_typer(user_groups_app)
app.add_typer(
    slas_app,
    name="slas",
    help="Manage SLAs belonging to a specific user group",
)
