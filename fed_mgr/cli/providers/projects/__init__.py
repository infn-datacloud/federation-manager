"""Module with the user groups subapp."""

import typer

from fed_mgr.cli.providers.projects.commands import app as projects_app
from fed_mgr.cli.providers.projects.regions import app as regions_app

app = typer.Typer()
app.add_typer(projects_app)
app.add_typer(
    regions_app,
    name="regions",
    help="Connect or disconnect regions to/from a specific project",
)
