"""Module with the user groups subapp."""

import typer

from fed_mgr.cli.identity_providers.commands import app as idps_app
from fed_mgr.cli.identity_providers.user_groups import app as user_groups_app

app = typer.Typer()
app.add_typer(idps_app)
app.add_typer(
    user_groups_app,
    name="user_groups",
    help="Manage user groups belonging to a specific identity provider",
)
