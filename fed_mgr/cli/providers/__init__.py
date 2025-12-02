"""Module with the user groups subapp."""

import typer

from fed_mgr.cli.providers.commands import app as providers_app
from fed_mgr.cli.providers.identity_providers import app as idps_app
from fed_mgr.cli.providers.projects import app as projects_app
from fed_mgr.cli.providers.regions import app as regions_app

app = typer.Typer()
app.add_typer(providers_app)
app.add_typer(
    idps_app,
    name="idps",
    help="Connect or disconnect identity provides to/from a specific provider",
)
app.add_typer(
    regions_app,
    name="regions",
    help="Manage regions belonging to a specific provider",
)
app.add_typer(
    projects_app,
    name="projects",
    help="Manage projects belonging to a specific provider",
)
