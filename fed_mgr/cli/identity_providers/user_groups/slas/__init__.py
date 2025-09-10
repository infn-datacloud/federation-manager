"""Module with the SLA subapp."""

import typer

from fed_mgr.cli.identity_providers.user_groups.slas.commands import app as slas_app
from fed_mgr.cli.identity_providers.user_groups.slas.projects import app as projects_app

app = typer.Typer()
app.add_typer(slas_app)
app.add_typer(
    projects_app,
    name="projects",
    help="Connect or disconnect projects to/from a specific SLA",
)
